# iOS Integration Guide

## Build MNN for iOS

### Prerequisites

- Xcode 12.0+
- iOS 8.0+ deployment target
- CMake 3.10+

### Build Steps

#### 1. Clone MNN Repository

```bash
git clone https://github.com/alibaba/MNN.git
cd MNN
```

#### 2. Build MNN Framework

**Standard Build:**

```bash
sh package_scripts/ios/buildiOS.sh
```

**Build with Options:**

```bash
sh package_scripts/ios/buildiOS.sh "-DMNN_ARM82=ON \
  -DMNN_METAL=ON \
  -DMNN_BUILD_LLM=ON \
  -DMNN_LOW_MEMORY=ON"
```

**Common Build Options:**
- `MNN_METAL=ON` - Enable Metal GPU support (recommended)
- `MNN_ARM82=ON` - Enable ARM v8.2 optimizations (FP16, dot product)
- `MNN_BUILD_LLM=ON` - Enable LLM support
- `MNN_LOW_MEMORY=ON` - Enable low memory mode
- `MNN_SUPPORT_TRANSFORMER_FUSE=ON` - Enable transformer optimizations
- `MNN_CPU_WEIGHT_DEQUANT_GEMM=ON` - Enable weight dequantization
- `MNN_BUILD_DIFFUSION=ON` - Enable diffusion model support
- `MNN_BUILD_AUDIO=ON` - Enable audio processing
- `MNN_BUILD_OPENCV=ON` - Enable OpenCV support

#### 3. Locate Build Artifacts

After building, the framework is located at:
```
MNN-iOS-CPU-GPU/Static/MNN.framework
```

## Xcode Integration

### 1. Add Framework to Project

**Method 1: Drag and Drop**
1. Drag `MNN.framework` into your Xcode project
2. Ensure "Copy items if needed" is checked
3. Add to target

**Method 2: Manual Link**
1. In project settings, go to "General" tab
2. Under "Frameworks, Libraries, and Embedded Content"
3. Click "+" and add `MNN.framework`

### 2. Configure Build Settings

**Add Header Search Path:**
```
$(PROJECT_DIR)/MNN.framework/Headers
```

**Link Frameworks:**
- MNN.framework
- Accelerate.framework
- Metal.framework (if using GPU)
- MetalPerformanceShaders.framework (if using GPU)

### 3. Update Deployment Target

Set minimum deployment target to iOS 8.0+ in project settings.

## Swift Integration

### 1. Create Bridging Header

Create `YourApp-Bridging-Header.h`:

```objc
#ifndef YourApp_Bridging_Header_h
#define YourApp_Bridging_Header_h

#import <MNN/Interpreter.hpp>
#import <MNN/Tensor.hpp>
#import <MNN/ImageProcess.hpp>

#endif
```

### 2. Create Objective-C++ Wrapper

Create `MNNWrapper.mm`:

```objc
#import <Foundation/Foundation.h>
#import <MNN/Interpreter.hpp>
#import <MNN/Tensor.hpp>

@interface MNNWrapper : NSObject

- (instancetype)initWithModelPath:(NSString *)modelPath;
- (void)createSession;
- (NSArray<NSNumber *> *)runInference:(NSArray<NSNumber *> *)input;
- (void)cleanup;

@end

@implementation MNNWrapper {
    std::shared_ptr<MNN::Interpreter> interpreter;
    MNN::Session *session;
}

- (instancetype)initWithModelPath:(NSString *)modelPath {
    self = [super init];
    if (self) {
        const char *path = [modelPath UTF8String];
        interpreter.reset(MNN::Interpreter::createFromFile(path));
        if (!interpreter) {
            return nil;
        }
    }
    return self;
}

- (void)createSession {
    MNN::ScheduleConfig config;
    config.type = MNN_FORWARD_METAL; // or MNN_FORWARD_CPU
    config.numThread = 4;
    
    MNN::BackendConfig backendConfig;
    backendConfig.precision = MNN::BackendConfig::Precision_Low; // FP16
    backendConfig.power = MNN::BackendConfig::Power_High;
    config.backendConfig = &backendConfig;
    
    session = interpreter->createSession(config);
}

- (NSArray<NSNumber *> *)runInference:(NSArray<NSNumber *> *)input {
    // Get input tensor
    MNN::Tensor *inputTensor = interpreter->getSessionInput(session, nullptr);
    
    // Copy input data
    auto inputData = inputTensor->host<float>();
    for (int i = 0; i < input.count; i++) {
        inputData[i] = [input[i] floatValue];
    }
    
    // Run inference
    interpreter->runSession(session);
    
    // Get output tensor
    MNN::Tensor *outputTensor = interpreter->getSessionOutput(session, nullptr);
    auto outputData = outputTensor->host<float>();
    
    // Convert to NSArray
    NSMutableArray *output = [NSMutableArray array];
    for (int i = 0; i < outputTensor->elementSize(); i++) {
        [output addObject:@(outputData[i])];
    }
    
    return output;
}

- (void)cleanup {
    if (interpreter) {
        interpreter->releaseSession(session);
        interpreter->releaseModel();
    }
}

@end
```

### 3. Use in Swift

```swift
import UIKit

class ModelInference {
    private var mnnWrapper: MNNWrapper?
    
    func loadModel(path: String) {
        mnnWrapper = MNNWrapper(modelPath: path)
        mnnWrapper?.createSession()
    }
    
    func runInference(input: [Float]) -> [Float]? {
        let inputNumbers = input.map { NSNumber(value: $0) }
        guard let output = mnnWrapper?.runInference(inputNumbers) else {
            return nil
        }
        return output.map { $0.floatValue }
    }
    
    deinit {
        mnnWrapper?.cleanup()
    }
}

// Usage
let model = ModelInference()
let modelPath = Bundle.main.path(forResource: "model", ofType: "mnn")!
model.loadModel(path: modelPath)

let input: [Float] = [1.0, 2.0, 3.0, 4.0]
if let output = model.runInference(input: input) {
    print("Output: \(output)")
}
```

## Objective-C Integration

### Complete Example

**MNNInference.h:**

```objc
#import <Foundation/Foundation.h>

@interface MNNInference : NSObject

- (instancetype)initWithModelPath:(NSString *)modelPath;
- (void)setupWithBackend:(NSString *)backend threads:(int)threads;
- (NSArray<NSNumber *> *)predict:(NSArray<NSNumber *> *)input;

@end
```

**MNNInference.mm:**

```objc
#import "MNNInference.h"
#import <MNN/Interpreter.hpp>
#import <MNN/Tensor.hpp>

@interface MNNInference() {
    std::shared_ptr<MNN::Interpreter> _interpreter;
    MNN::Session *_session;
}
@end

@implementation MNNInference

- (instancetype)initWithModelPath:(NSString *)modelPath {
    self = [super init];
    if (self) {
        const char *path = [modelPath UTF8String];
        _interpreter.reset(MNN::Interpreter::createFromFile(path));
    }
    return self;
}

- (void)setupWithBackend:(NSString *)backend threads:(int)threads {
    MNN::ScheduleConfig config;
    
    if ([backend isEqualToString:@"metal"]) {
        config.type = MNN_FORWARD_METAL;
    } else {
        config.type = MNN_FORWARD_CPU;
    }
    
    config.numThread = threads;
    
    MNN::BackendConfig backendConfig;
    backendConfig.precision = MNN::BackendConfig::Precision_Low;
    backendConfig.power = MNN::BackendConfig::Power_High;
    config.backendConfig = &backendConfig;
    
    _session = _interpreter->createSession(config);
}

- (NSArray<NSNumber *> *)predict:(NSArray<NSNumber *> *)input {
    MNN::Tensor *inputTensor = _interpreter->getSessionInput(_session, nullptr);
    
    auto data = inputTensor->host<float>();
    for (int i = 0; i < input.count; i++) {
        data[i] = [input[i] floatValue];
    }
    
    _interpreter->runSession(_session);
    
    MNN::Tensor *outputTensor = _interpreter->getSessionOutput(_session, nullptr);
    auto outData = outputTensor->host<float>();
    
    NSMutableArray *result = [NSMutableArray array];
    for (int i = 0; i < outputTensor->elementSize(); i++) {
        [result addObject:@(outData[i])];
    }
    
    return result;
}

- (void)dealloc {
    if (_interpreter) {
        _interpreter->releaseSession(_session);
        _interpreter->releaseModel();
    }
}

@end
```

## Image Processing

### Using MNN's ImageProcess

```objc
#import <MNN/ImageProcess.hpp>

- (void)preprocessImage:(UIImage *)image toTensor:(MNN::Tensor *)tensor {
    // Convert UIImage to CVPixelBuffer
    CVPixelBufferRef pixelBuffer = [self pixelBufferFromImage:image];
    
    // Configure image process
    MNN::CV::ImageProcess::Config config;
    config.filterType = MNN::CV::BILINEAR;
    
    // Set mean and normal
    float mean[3] = {127.5f, 127.5f, 127.5f};
    float normal[3] = {0.00784314f, 0.00784314f, 0.00784314f};
    ::memcpy(config.mean, mean, sizeof(mean));
    ::memcpy(config.normal, normal, sizeof(normal));
    
    config.sourceFormat = MNN::CV::RGBA;
    config.destFormat = MNN::CV::RGB;
    
    // Create ImageProcess
    std::shared_ptr<MNN::CV::ImageProcess> process(
        MNN::CV::ImageProcess::create(config));
    
    // Process image
    MNN::CV::Matrix matrix;
    matrix.setScale(1.0f, 1.0f);
    process->setMatrix(matrix);
    
    process->convert((uint8_t*)CVPixelBufferGetBaseAddress(pixelBuffer),
                    (int)CVPixelBufferGetWidth(pixelBuffer),
                    (int)CVPixelBufferGetHeight(pixelBuffer),
                    0,
                    tensor);
}
```

## Metal GPU Configuration

### Enable Metal Backend

```objc
MNN::ScheduleConfig config;
config.type = MNN_FORWARD_METAL;
config.numThread = 1; // Metal uses single thread

MNN::BackendConfig backendConfig;
backendConfig.precision = MNN::BackendConfig::Precision_Low; // FP16
backendConfig.power = MNN::BackendConfig::Power_High;        // High performance
backendConfig.memory = MNN::BackendConfig::Memory_Normal;    // Normal memory usage

config.backendConfig = &backendConfig;

_session = _interpreter->createSession(config);
```

## Performance Optimization

### 1. Use Metal When Available

Metal provides significantly better performance than CPU on iOS:
- 3-5x faster for convolution operations
- Better energy efficiency
- Optimized for Apple GPUs

### 2. Enable ARM v8.2 Optimizations

Build with `-DMNN_ARM82=ON` for devices with A11+ chips:
- FP16 acceleration
- Dot product instructions
- 2x performance improvement

### 3. Adjust Thread Count

```objc
// For CPU backend
config.numThread = [[NSProcessInfo processInfo] processorCount];
```

### 4. Use Appropriate Precision

```objc
// FP16 (faster, slight accuracy loss)
backendConfig.precision = MNN::BackendConfig::Precision_Low;

// FP32 (slower, full accuracy)
backendConfig.precision = MNN::BackendConfig::Precision_Normal;
```

## Troubleshooting

### Common Issues

**1. Framework Not Found**
- Verify framework is in correct location
- Check framework search paths in build settings
- Ensure framework is embedded in app bundle

**2. Symbol Not Found**
- Check that all required frameworks are linked
- Verify Metal/MetalPerformanceShaders for GPU support
- Ensure proper C++ standard library linkage

**3. Model Loading Fails**
- Verify model file is in app bundle
- Check file path and permissions
- Ensure model is valid MNN format

**4. Poor Performance**
- Enable Metal backend for GPU acceleration
- Build with ARM v8.2 optimizations
- Use FP16 precision
- Verify appropriate thread count

## Example Project Structure

```
MNNiOSApp/
├── MNNiOSApp/
│   ├── Models/
│   │   └── model.mnn
│   ├── MNN.framework/
│   │   ├── Headers/
│   │   └── MNN
│   ├── Inference/
│   │   ├── MNNWrapper.mm
│   │   └── MNNInference.mm
│   ├── ViewController.swift
│   └── YourApp-Bridging-Header.h
├── MNNiOSApp.xcodeproj
└── Podfile (optional)
```

## SwiftUI Integration

```swift
import SwiftUI

class ModelViewModel: ObservableObject {
    @Published var result: String = ""
    private var inference: ModelInference?
    
    init() {
        let path = Bundle.main.path(forResource: "model", ofType: "mnn")!
        inference = ModelInference()
        inference?.loadModel(path: path)
    }
    
    func predict(input: [Float]) {
        if let output = inference?.runInference(input: input) {
            result = "Output: \(output)"
        }
    }
}

struct ContentView: View {
    @StateObject private var viewModel = ModelViewModel()
    
    var body: some View {
        VStack {
            Text(viewModel.result)
                .padding()
            
            Button("Run Inference") {
                viewModel.predict(input: [1.0, 2.0, 3.0])
            }
        }
    }
}
```

## Reference

- [MNN iOS Build Script](https://github.com/alibaba/MNN/blob/master/package_scripts/ios/buildiOS.sh)
- [MNN iOS Demo](https://github.com/alibaba/MNN/tree/master/demo/ios)
- [MNN iOS LLM App](https://github.com/alibaba/MNN/tree/master/apps/iOS/MNNLLMChat)
