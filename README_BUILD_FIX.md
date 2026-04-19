# Fix для ошибки "C compiler cannot create executables" на NDK r25b

## Проблема

При сборке приложения с использованием NDK r25b возникает ошибка:
```
checking whether the C compiler works... no
configure: error: C compiler cannot create executables
```

Это происходит из-за того, что python-for-android не может корректно определить компилятор clang из NDK r25b.

## Решение

### Вариант 1: Обновление GitHub Actions workflow (рекомендуется для CI/CD)

В файл `.github/workflows/build.yml` добавлен шаг явной настройки компилятора:

```yaml
- name: Configure C compiler for NDK r25b
  run: |
    export CC=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android21-clang
    export CXX=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android21-clang++
    export AR=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-ar
    export RANLIB=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-ranlib
    export STRIP=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip

    echo "CC=$CC" >> $GITHUB_ENV
    echo "CXX=$CXX" >> $GITHUB_ENV
    echo "AR=$AR" >> $GITHUB_ENV
    echo "RANLIB=$RANLIB" >> $GITHUB_ENV
    echo "STRIP=$STRIP" >> $GITHUB_ENV
```

### Вариант 2: Использование скрипта сборки (для локальной разработки)

Запустите скрипт `build_fix.sh`, который явно указывает пути к компиляторам:

```bash
./build_fix.sh
```

### Вариант 3: Ручная установка переменных окружения

Перед запуском buildozer установите переменные окружения:

```bash
export ANDROID_NDK_HOME=$HOME/.buildozer/android/platform/android-ndk-r25b
export CC=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android21-clang
export CXX=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android21-clang++
export AR=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-ar
export RANLIB=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-ranlib
export STRIP=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip

buildozer android clean
buildozer android debug
```

### Вариант 4: Обновление python-for-android

Обновите python-for-android до последней версии develop:

```bash
pip install --upgrade git+https://github.com/kivy/python-for-android.git@develop
```

## Дополнительные исправления в buildozer.spec

В файл `buildozer.spec` уже внесены следующие изменения:

1. `p4a.branch = develop` - используется ветка develop python-for-android с лучшей поддержкой NDK r25b
2. `android.ndk = 25b` - стабильная версия NDK для python-for-android
3. `android.archs = arm64-v8a` - сборка только для 64-битной архитектуры ARM
4. `android.copy_libs = 1` - копирование библиотек вместо создания libpymodules.so
5. `p4a.local_recipes = local_recipes` - использование локальных рецептов для совместимости
6. `android.enable_androidx = True` - поддержка AndroidX для современных версий Android
7. `android.request_legacy_external_storage = True` - совместимость с Android 10-12

## Проверка после сборки

После успешной сборки проверьте APK на устройстве POCO F3 с Android 13:

```bash
adb install -r bin/englishlearning-0.1.0-debug.apk
adb logcat | grep python
```

## Ссылки

- [Issue: NDK r25b compiler detection](https://github.com/kivy/python-for-android/issues)
- [Android NDK r25 Release Notes](https://developer.android.com/ndk/downloads/revision_history)
