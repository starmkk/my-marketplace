"""
하네스 엔지니어링 — ExperimentConfig 템플릿

이 파일은 새 프로젝트 생성 시 src/utils/config.py의 기반이 된다.
{placeholder}는 프로젝트별 값으로 치환한다.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """모델 아키텍처 및 파인튜닝 설정"""

    name: str = "{base_model}"
    pretrained_path: str = "{base_model}"
    local_models_dir: str = ""
    torch_dtype: str = "bfloat16"

    # LoRA 설정
    use_lora: bool = False
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list[str] = field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"]
    )


@dataclass
class DataConfig:
    """데이터 파이프라인 설정"""

    dataset_name: str = "{dataset}"
    train_jsonl: str = ""
    val_jsonl: str = ""
    test_jsonl: str | list[str] = ""

    batch_size: int = 4
    val_batch_size: int = -1
    num_workers: int = 4

    max_train_samples: int = -1
    max_val_samples: int = -1
    max_test_samples: int = -1

    def get_val_batch_size(self) -> int:
        return self.batch_size if self.val_batch_size == -1 else self.val_batch_size

    def get_test_jsonl_list(self) -> list[str]:
        if isinstance(self.test_jsonl, list):
            return self.test_jsonl
        return [self.test_jsonl]


@dataclass
class TrainingConfig:
    """학습 루프 설정"""

    epochs: int = 3
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0

    optimizer: str = "adamw"
    scheduler: str = "cosine"
    warmup_steps: int = 100

    gradient_accumulation_steps: int = 1
    mixed_precision: str = "bf16"

    save_every_n_epochs: int = 1
    eval_every_n_steps: int = 500
    early_stopping_patience: int = 3
    total_steps: int = -1

    def get_effective_batch_size(self, batch_size: int, num_gpus: int = 1) -> int:
        return batch_size * self.gradient_accumulation_steps * num_gpus


@dataclass
class HardwareConfig:
    """하드웨어 및 디바이스 설정"""

    device: str = "cuda"
    precision: str = "bfloat16"
    num_gpus: int = 1
    gradient_checkpointing: bool = False


@dataclass
class ExperimentConfig:
    """전체 실험 설정 — YAML 파일과 1:1 매핑"""

    experiment_name: str = "{project}_{dataset}"
    output_dir: str = "experiments/{dataset}"
    seed: int = 42

    model: ModelConfig = field(default_factory=ModelConfig)
    data: DataConfig = field(default_factory=DataConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> ExperimentConfig:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"설정 파일 없음: {path}")
        with open(path) as f:
            raw = yaml.safe_load(f)
        return cls._from_dict(raw)

    @classmethod
    def _from_dict(cls, d: dict[str, Any]) -> ExperimentConfig:
        config = cls()
        for key in ("experiment_name", "output_dir", "seed"):
            if key in d:
                setattr(config, key, d[key])
        section_map = {
            "model": (ModelConfig, config.model),
            "data": (DataConfig, config.data),
            "training": (TrainingConfig, config.training),
            "hardware": (HardwareConfig, config.hardware),
        }
        for section_key, (section_cls, section_obj) in section_map.items():
            if section_key in d and isinstance(d[section_key], dict):
                for k, v in d[section_key].items():
                    if hasattr(section_obj, k):
                        setattr(section_obj, k, v)
                    else:
                        logger.warning(f"알 수 없는 설정 키: {section_key}.{k}")
        return config

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

    def to_yaml(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        logger.info(f"설정 저장: {path}")

    def validate(self) -> None:
        # MPS에서 bfloat16 제한
        if self.hardware.device == "mps":
            if self.model.torch_dtype == "bfloat16":
                logger.warning("MPS는 bfloat16 미지원 → float32로 전환")
                self.model.torch_dtype = "float32"
            if self.hardware.precision == "bfloat16":
                self.hardware.precision = "float32"
            if self.training.mixed_precision == "bf16":
                logger.warning("MPS는 bf16 mixed precision 미지원 → 'no'로 전환")
                self.training.mixed_precision = "no"

        assert self.training.learning_rate > 0
        assert self.training.epochs > 0
        assert self.data.batch_size > 0
        assert self.training.gradient_accumulation_steps > 0

    def copy(self) -> ExperimentConfig:
        return copy.deepcopy(self)

    def summary(self) -> str:
        eff_batch = self.training.get_effective_batch_size(
            self.data.batch_size, self.hardware.num_gpus
        )
        lines = [
            f"=== {self.experiment_name} ===",
            f"모델: {self.model.name} (LoRA={self.model.use_lora})",
            f"디바이스: {self.hardware.device} (dtype={self.model.torch_dtype})",
            f"배치: {self.data.batch_size} x {self.training.gradient_accumulation_steps} "
            f"x {self.hardware.num_gpus}GPU = {eff_batch} (effective)",
            f"학습률: {self.training.learning_rate}, Epochs: {self.training.epochs}",
            f"출력: {self.output_dir}",
        ]
        return "\n".join(lines)
