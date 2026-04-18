from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory
import shutil
import os

class OpensslRecipe(Recipe):
    version = '1.1.1w'
    url = '/home/maxim/.buildozer/android/platform/build-arm64-v8a/packages/openssl/openssl-1.1.1w.tar.gz'
    sha256 = 'a0c3fe60c5c010f85155088a4e896f4d3f6e3f8e8e8e8e8e8e8e8e8e8e8e8e8e'  # заглушка
    
    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        return env
    
    def prebuild_arch(self, arch):
        # Пропускаем скачивание, если папка уже есть
        build_dir = self.get_build_dir(arch.arch)
        if os.path.exists(os.path.join(build_dir, 'Configure')):
            print(f'Openssl already extracted in {build_dir}, skipping')
            return
        super().prebuild_arch(arch)

recipe = OpensslRecipe()
