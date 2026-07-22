---
name: pytorch-harness
description: "PyTorch 하네스 엔지니어링 프로젝트 템플릿 생성기. 신규 PyTorch 프로젝트를 Config-Driven + Factory Pattern 기반의 하네스 구조로 스캐폴딩한다. 'pytorch 프로젝트 템플릿', '신규 프로젝트 생성', '하네스 프로젝트 만들어줘', 'scaffold', 'new project template' 등의 키워드가 나오면 트리거한다."
---

# PyTorch 하네스 엔지니어링 — 프로젝트 템플릿 생성기

사용자가 새로운 PyTorch 프로젝트 템플릿을 요청하면, 아래 하네스 엔지니어링 방법론에 따라 전체 프로젝트 구조를 생성한다.

## 사용자에게 먼저 확인할 정보

템플릿 생성 전 반드시 다음을 확인하라:

1. **프로젝트 이름** (예: `speech-recognition`, `image-classifier`)
2. **태스크 유형** (예: ASR, 이미지 분류, 객체 탐지, NLP, 멀티모달 등)
3. **베이스 모델** (예: `google/gemma-4-E2B-it`, `openai/whisper-large-v3`, 커스텀 모델)
4. **데이터셋** (예: LibriSpeech, ImageNet, 커스텀 데이터)
5. **타깃 하드웨어** (예: Mac M4, RTX 3090, A100, 온디바이스)
6. **파인튜닝 방식** (예: LoRA, Full Fine-tuning, QLoRA)
7. **생성 경로** (기본: 현재 디렉토리)

## 하네스 엔지니어링 방법론

### 핵심 원칙

1. **Config-Driven**: 모든 하이퍼파라미터는 YAML → dataclass(ExperimentConfig) 경로로 관리
2. **Factory Pattern**: `create_model(config)`, `create_dataloaders(config)` 패턴 사용
3. **Layered Architecture**: 5계층 (모델 → 데이터 → 학습 → 추론 → 평가)
4. **Stage Testing**: `@pytest.mark.stage1` ~ `stage4`로 단계별 테스트
5. **Preprocessor 분리**: `training=True/False`로 증강 자동 전환
6. **Hardware-Aware Config**: Mac/CUDA/TPU별 별도 YAML 프로파일

### 디렉토리 구조 (반드시 이 구조를 따른다)

```
{project_name}/
├── configs/
│   └── experiments/                    # YAML 실험 설정 (하드웨어별)
│       ├── {task}_{dataset}_m4_debug.yaml      # Mac M4 디버그용
│       ├── {task}_{dataset}_rtx3090.yaml       # RTX 3090 학습용
│       └── {task}_{dataset}_a100.yaml          # A100 대규모 학습용
├── src/
│   ├── __init__.py
│   ├── models/                         # [Layer 1] 모델 아키텍처
│   │   ├── __init__.py
│   │   └── factory.py                  # create_model(config) → 모델+프로세서+토크나이저
│   ├── data/                           # [Layer 2] 데이터 파이프라인
│   │   ├── __init__.py
│   │   ├── dataset.py                  # torch.utils.data.Dataset 구현
│   │   ├── collator.py                 # DataCollator (동적 패딩)
│   │   └── factory.py                  # create_dataloaders(config) → train/val/test 로더
│   ├── training/                       # [Layer 3] 학습 파이프라인
│   │   ├── __init__.py
│   │   ├── trainer.py                  # 학습 루프 (train/validate/save)
│   │   └── utils.py                    # 옵티마이저/스케줄러 생성
│   ├── inference/                      # [Layer 4] 추론 엔진
│   │   └── __init__.py
│   ├── evaluation/                     # [Layer 5] 평가
│   │   ├── __init__.py
│   │   ├── evaluator.py               # 평가 루프
│   │   └── metrics.py                  # 태스크별 메트릭 (WER/CER/Accuracy 등)
│   └── utils/                          # 유틸리티
│       ├── __init__.py
│       └── config.py                   # ExperimentConfig (YAML ↔ dataclass)
├── models/                             # HuggingFace 모델 로컬 저장소
├── tests/                              # pytest 하네스 (Stage 마커)
│   ├── conftest.py                     # 공통 fixture + Stage 마커 등록
│   ├── test_stage1_env.py              # Stage 1: 환경 검증
│   ├── test_stage2_data.py             # Stage 2: 데이터 파이프라인
│   ├── test_stage3_model.py            # Stage 3: 모델 아키텍처
│   └── test_stage4_training.py         # Stage 4: 학습 파이프라인
├── experiments/
│   └── {dataset}/                      # 실험 출력
│       ├── checkpoints/                # 체크포인트
│       ├── tensorboard/                # TensorBoard 로그
│       └── report/                     # 테스트 HTML 리포트
├── scripts/
│   ├── train.py                        # 학습 엔트리포인트
│   └── merge_lora.py                   # LoRA 합산 (해당 시)
├── run.sh                              # 통합 실행 스크립트
├── requirements.txt                    # Python 의존성
├── pyproject.toml                      # ruff lint + 프로젝트 메타데이터
├── pytest.ini                          # 테스트 마커 설정
├── .gitignore
├── README.md
├── CLAUDE.md                           # Claude Code 프로젝트 지침
└── ARCHITECTURE.md                     # 아키텍처 문서
```

### 파일별 생성 규칙

#### 1. `src/utils/config.py` — ExperimentConfig

```python
"""
{project_name} 하네스 — ExperimentConfig

YAML 설정 파일을 Python dataclass로 매핑하는 Config-Driven 시스템.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import yaml

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
    # JSONL 경로 (프로젝트 루트 기준 상대경로)
    train_jsonl: str = ""
    val_jsonl: str = ""
    test_jsonl: str | list[str] = ""
    batch_size: int = 4
    val_batch_size: int = -1  # -1이면 batch_size와 동일
    num_workers: int = 4
    max_train_samples: int = -1  # -1 = 전체 사용
    max_val_samples: int = -1
    max_test_samples: int = -1

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
    mixed_precision: str = "bf16"  # "bf16" | "fp16" | "no"
    save_every_n_epochs: int = 1
    eval_every_n_steps: int = 500
    early_stopping_patience: int = 3
    total_steps: int = -1  # -1 = 자동 계산

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
    experiment_name: str = "{project_name}_{dataset}"
    output_dir: str = "experiments/{dataset}"
    seed: int = 42
    model: ModelConfig = field(default_factory=ModelConfig)
    data: DataConfig = field(default_factory=DataConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> ExperimentConfig:
        ...  # YAML 로드 → _from_dict

    def to_yaml(self, path: str | Path) -> None:
        ...  # 딕셔너리 → YAML 저장

    def validate(self) -> None:
        ...  # MPS/CUDA 호환성, 파라미터 범위 검증
```

#### 2. YAML 실험 설정

하드웨어별로 3개의 프로파일을 생성한다:

- **m4_debug.yaml**: `device: mps`, `float32`, `batch_size: 1`, `grad_accum: 4`, `max_samples: 50`
- **rtx3090.yaml**: `device: cuda`, `bfloat16`, `batch_size: 8`, `grad_accum: 2`
- **a100.yaml**: `device: cuda`, `bfloat16`, `batch_size: 16`, `grad_accum: 1`

각 YAML 파일 상단에 메모리 예산, effective batch size, 근거를 주석으로 명시한다.

#### 3. `run.sh` — 통합 실행 스크립트

지원 모드:
- `--config <yaml>`: 학습 실행
- `--eval --config <yaml> --checkpoint <path>`: 평가만 실행
- `--test [--stage N]`: pytest 실행 (HTML 리포트 자동 생성)
- `--lint [--fix]`: ruff lint + format
- `--merge --config <yaml>`: LoRA 합산 (해당 시)

#### 4. `pytest.ini` + `conftest.py`

Stage 마커:
- `stage1`: 환경 검증 (import, GPU, 설정 로드)
- `stage2`: 데이터 파이프라인 (Dataset, DataLoader, 전처리)
- `stage3`: 모델 아키텍처 (모델 로드, forward pass, LoRA 적용)
- `stage4`: 학습 파이프라인 (1 step 학습, 체크포인트 저장/로드)

#### 5. `pyproject.toml`

ruff 설정 포함:
- `line-length = 120`
- `select = ["E", "F", "W", "I"]`
- `known-first-party = ["src"]`

#### 6. 체크포인트 네이밍 규칙

```
model_{epoch:03d}_{val_loss:.4f}_{val_metric:.2f}.pt
```
예: `model_003_0.2451_0.95.pt`

#### 7. `.gitignore`

```gitignore
# 모델/데이터/실험 (대용량)
models/
data/
experiments/*/checkpoints/
experiments/*/tensorboard/
*.pt
*.bin
*.safetensors

# Python
__pycache__/
*.egg-info/
.venv/
dist/
build/

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

### 생성 절차

1. 사용자에게 필요한 정보 확인 (프로젝트명, 태스크, 모델, 데이터셋, 하드웨어)
2. 각 단계별로 **사용자 승인을 받은 후** 진행 (feedback_approval_workflow 참조)
3. 디렉토리 구조 생성
4. `src/utils/config.py` (ExperimentConfig) 생성
5. `src/models/factory.py` 생성
6. `src/data/dataset.py`, `collator.py`, `factory.py` 생성
7. `src/training/trainer.py`, `utils.py` 생성
8. `src/evaluation/evaluator.py`, `metrics.py` 생성
9. YAML 설정 파일 생성 (하드웨어별)
10. `run.sh` 생성
11. `tests/conftest.py` + Stage 테스트 파일 생성
12. `pyproject.toml`, `pytest.ini`, `requirements.txt` 생성
13. `.gitignore`, `README.md`, `CLAUDE.md`, `ARCHITECTURE.md` 생성
14. `ruff check` + `ruff format`으로 lint 검증

### 태스크별 커스터마이징

태스크 유형에 따라 자동 조정되는 항목:

| 항목 | ASR | 이미지 분류 | 객체 탐지 | NLP |
|------|-----|------------|----------|-----|
| 메트릭 | WER, CER | Accuracy, F1 | mAP, IoU | BLEU, ROUGE |
| 데이터 전처리 | 오디오 로드+리샘플링 | 이미지 리사이즈+증강 | 이미지+박스 변환 | 토큰화 |
| 추가 의존성 | soundfile, librosa, jiwer | torchvision, albumentations | torchvision, pycocotools | datasets, evaluate |
| DataCollator | 동적 오디오 패딩 | 이미지 배치 스택 | 가변 박스 패딩 | 동적 텍스트 패딩 |

### 참고: 현재 프로젝트 (Gemma-4-E2B-it) 기반

이 템플릿은 `Gemma-4-E2B-it.main` 프로젝트의 실제 구현을 기반으로 한다.
검증된 패턴: Config-Driven YAML, Factory Pattern, Stage Testing, 하드웨어별 프로파일링.
