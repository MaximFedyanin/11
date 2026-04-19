# Fix для ошибки "C compiler cannot create executables" на NDK r25b

## Проблема

При сборке приложения с использованием NDK r25b возникает ошибка:
```
checking whether the C compiler works... no
configure: error: C compiler cannot create executables
```

Это происходит из-за того, что python-for-android не может корректно определить компилятор clang из NDK r25b.

## Решение

### Вариант 1: Использование скрипта сборки (рекомендуется)

Запустите скрипт `build_fix.sh`, который явно указывает пути к компиляторам:

```bash
./build_fix.sh
```

### Вариант 2: Ручная установка переменных окружения

Перед запуском buildozer установите переменные окружения:

```bash
export CC=/home/runner/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin/armv7a-linux-androideabi21-clang
export CXX=/home/runner/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin/armv7a-linux-androideabi21-clang++
export AR=/home/runner/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-ar
export RANLIB=/home/runner/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-ranlib
export STRIP=/home/runner/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip

buildozer android clean
buildozer android debug
```

### Вариант 3: Обновление python-for-android

Обновите python-for-android до последней версии develop:

```bash
pip install --upgrade git+https://github.com/kivy/python-for-android.git@develop
```

### Вариант 4: Изменение архитектуры сборки

Если проблема сохраняется, попробуйте собрать только для arm64-v8a:

В файле `buildozer.spec` измените:
```spec
android.archs = arm64-v8a
```

## Дополнительные исправления в buildozer.spec

В файл `buildozer.spec` были внесены следующие изменения:

1. Добавлен флаг `--disable-ndk-deployment` в `p4a.extra_args`
2. Добавлена опция `p4a.autofix = True` для автоматического исправления проблем
3. Исключены директории сборки из исходников

## Проверка после сборки

После успешной сборки проверьте APK на устройстве POCO F3 с Android 13:

```bash
adb install -r bin/englishlearning-0.1.0-debug.apk
adb logcat | grep python
```

## Ссылки

- [Issue: NDK r25b compiler detection](https://github.com/kivy/python-for-android/issues)
- [Android NDK r25 Release Notes](https://developer.android.com/ndk/downloads/revision_history)
