# Android Integration Guide

## Build MNN for Android

### Prerequisites

- Android NDK r21+
- CMake 3.10+
- Android Studio (optional, for app development)

### Build Steps

#### 1. Clone MNN Repository

```bash
git clone https://github.com/alibaba/MNN.git
cd MNN
```

#### 2. Build Native Library

**For ARM64-v8a (64-bit):**

```bash
cd project/android
mkdir build_64
cd build_64
../build_64.sh
```

**For ARMv7a (32-bit):**

```bash
cd project/android
mkdir build_32
cd build_32
../build_32.sh
```

**Custom Build with Options:**

```bash
../build_64.sh "-DMNN_OPENCL=ON -DMNN_VULKAN=ON -DMNN_ARM82=ON"
```

**Common Build Options:**
- `MNN_OPENCL=ON` - Enable OpenCL GPU support
- `MNN_VULKAN=ON` - Enable Vulkan GPU support
- `MNN_ARM82=ON` - Enable ARM v8.2 optimizations (FP16, dot product)
- `MNN_LOW_MEMORY=ON` - Enable low memory mode
- `MNN_BUILD_LLM=ON` - Enable LLM support
- `MNN_SUPPORT_TRANSFORMER_FUSE=ON` - Enable transformer optimizations
- `MNN_USE_LOGCAT=ON` - Enable logcat logging

#### 3. Locate Build Artifacts

After building, libraries are located in:
```
MNN/project/android/build_64/libs/arm64-v8a/
  ├── libMNN.so
  ├── libMNN_CL.so (if OpenCL enabled)
  ├── libMNN_Vulkan.so (if Vulkan enabled)
  └── libMNN_Express.so
```

## Android Studio Integration

### 1. Project Setup

**Add to `app/build.gradle`:**

```gradle
android {
    defaultConfig {
        ndk {
            abiFilters 'arm64-v8a', 'armeabi-v7a'
        }
    }
    
    sourceSets {
        main {
            jniLibs.srcDirs = ['libs']
        }
    }
}
```

### 2. Copy Libraries

Copy MNN libraries to your project:
```
YourApp/
└── app/
    └── src/
        └── main/
            ├── jniLibs/
            │   ├── arm64-v8a/
            │   │   └── libMNN.so
            │   └── armeabi-v7a/
            │       └── libMNN.so
            └── java/
```

### 3. Create JNI Wrapper

**C++ JNI Implementation (`native-lib.cpp`):**

```cpp
#include <jni.h>
#include <string>
#include <MNN/Interpreter.hpp>
#include <MNN/Tensor.hpp>

using namespace MNN;

extern "C" JNIEXPORT jlong JNICALL
Java_com_example_app_MNNWrapper_createInterpreter(
    JNIEnv* env, jobject thiz, jstring modelPath) {
    
    const char* path = env->GetStringUTFChars(modelPath, nullptr);
    Interpreter* interpreter = Interpreter::createFromFile(path);
    env->ReleaseStringUTFChars(modelPath, path);
    
    return reinterpret_cast<jlong>(interpreter);
}

extern "C" JNIEXPORT jlong JNICALL
Java_com_example_app_MNNWrapper_createSession(
    JNIEnv* env, jobject thiz, jlong interpreterPtr) {
    
    Interpreter* interpreter = reinterpret_cast<Interpreter*>(interpreterPtr);
    
    ScheduleConfig config;
    config.type = MNN_FORWARD_CPU;
    config.numThread = 4;
    
    Session* session = interpreter->createSession(config);
    return reinterpret_cast<jlong>(session);
}

extern "C" JNIEXPORT void JNICALL
Java_com_example_app_MNNWrapper_runInference(
    JNIEnv* env, jobject thiz, jlong interpreterPtr, 
    jlong sessionPtr, jfloatArray inputData) {
    
    Interpreter* interpreter = reinterpret_cast<Interpreter*>(interpreterPtr);
    Session* session = reinterpret_cast<Session*>(sessionPtr);
    
    // Get input tensor
    Tensor* inputTensor = interpreter->getSessionInput(session, nullptr);
    
    // Copy input data
    jfloat* data = env->GetFloatArrayElements(inputData, nullptr);
    memcpy(inputTensor->host<float>(), data, 
           inputTensor->size() * sizeof(float));
    env->ReleaseFloatArrayElements(inputData, data, 0);
    
    // Run inference
    interpreter->runSession(session);
}
```

**Java Wrapper (`MNNWrapper.java`):**

```java
package com.example.app;

public class MNNWrapper {
    static {
        System.loadLibrary("native-lib");
    }
    
    private long interpreterPtr;
    private long sessionPtr;
    
    public void loadModel(String modelPath) {
        interpreterPtr = createInterpreter(modelPath);
        sessionPtr = createSession(interpreterPtr);
    }
    
    public void runInference(float[] input) {
        runInference(interpreterPtr, sessionPtr, input);
    }
    
    private native long createInterpreter(String modelPath);
    private native long createSession(long interpreterPtr);
    private native void runInference(long interpreterPtr, 
                                     long sessionPtr, float[] input);
}
```

## GPU Backend Configuration

### OpenCL Backend

```cpp
ScheduleConfig config;
config.type = MNN_FORWARD_OPENCL;
config.numThread = 1; // GPU typically uses 1 thread
BackendConfig backendConfig;
backendConfig.precision = BackendConfig::Precision_Low; // FP16
backendConfig.power = BackendConfig::Power_High;
config.backendConfig = &backendConfig;

Session* session = interpreter->createSession(config);
```

### Vulkan Backend

```cpp
ScheduleConfig config;
config.type = MNN_FORWARD_VULKAN;
config.numThread = 1;
BackendConfig backendConfig;
backendConfig.precision = BackendConfig::Precision_Low;
config.backendConfig = &backendConfig;

Session* session = interpreter->createSession(config);
```

## Performance Tips

### 1. Thread Configuration

```cpp
config.numThread = 4; // Set based on device cores
```

### 2. Use ARM v8.2 Optimizations

Build with `-DMNN_ARM82=ON` for devices that support it.

### 3. Use GPU When Available

```cpp
// Try GPU first, fallback to CPU
ScheduleConfig config;
config.type = MNN_FORWARD_OPENCL;
Session* session = interpreter->createSession(config);

if (!session) {
    config.type = MNN_FORWARD_CPU;
    session = interpreter->createSession(config);
}
```

### 4. Memory Management

```cpp
// Use low memory mode
BackendConfig backendConfig;
backendConfig.memory = BackendConfig::Memory_Low;
config.backendConfig = &backendConfig;
```

## Troubleshooting

### Common Issues

**1. Library Not Found**
- Ensure `.so` files are in correct ABI directories
- Check `System.loadLibrary()` call

**2. UnsatisfiedLinkError**
- Verify JNI function signatures match Java declarations
- Check C++ name mangling with `extern "C"`

**3. Model Loading Fails**
- Verify model file path is accessible
- Check file permissions
- Ensure model is valid MNN format

**4. Performance Issues**
- Enable ARM v8.2 optimizations if supported
- Use GPU backend for compute-intensive models
- Adjust thread count based on device
- Enable low memory mode if needed

## Example App Structure

```
MNNAndroidApp/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/
│   │   │   │   └── com/example/app/
│   │   │   │       ├── MainActivity.java
│   │   │   │       └── MNNWrapper.java
│   │   │   ├── cpp/
│   │   │   │   ├── native-lib.cpp
│   │   │   │   └── CMakeLists.txt
│   │   │   ├── jniLibs/
│   │   │   │   ├── arm64-v8a/
│   │   │   │   │   └── libMNN.so
│   │   │   │   └── armeabi-v7a/
│   │   │   │       └── libMNN.so
│   │   │   └── assets/
│   │   │       └── model.mnn
│   │   └── androidTest/
│   └── build.gradle
└── gradle.properties
```
