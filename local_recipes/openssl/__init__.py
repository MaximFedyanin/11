from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory
import shutil
import os

class OpensslRecipe(Recipe):
    version = '1.1.1w'
    url = 'https://github.com/openssl/openssl/releases/download/OpenSSL_1_1_1w/openssl-1.1.1w.tar.gz'
    sha256 = 'cf3098950cb4d853ad95c0841f1f9c6d3dc102dccfcacd521d93925208b76ac8'

    def include_flags(self, arch):
        """Return include flags for the openssl recipe."""
        build_dir = self.get_build_dir(arch.arch)
        return ['-I{}'.format(os.path.join(build_dir, 'include'))]

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
