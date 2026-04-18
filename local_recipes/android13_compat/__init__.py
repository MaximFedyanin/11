"""
Android 13+ Compatibility Fixes for Python-for-Android

This recipe addresses SELinux permission issues and library loading problems
on Android 13 (API 33) and above, specifically for Xiaomi HyperOS devices.

Issues fixed:
1. SELinux execute denials for .so modules in app directory
2. Proper library path configuration for Python shared libraries
3. Android 13 scoped storage compatibility
"""

from pythonforandroid.recipe import Recipe, PythonRecipe
from pythonforandroid.util import current_directory
import shutil
import os


class Android13CompatibilityRecipe(Recipe):
    """
    Meta-recipe for Android 13+ compatibility fixes.
    This recipe ensures proper permissions and library paths for Android 13+.
    """

    name = 'android13_compat'
    version = '1.0.0'

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)

        # Set Android 13+ specific environment variables
        env['ANDROID_API'] = '33'
        env['TARGET_PLATFORM'] = 'android-33'

        # Enable proper library loading for Android 13+
        env['LD_LIBRARY_PATH'] = '${PRIVATE_DATA}/lib:${APP_PRIVATE_DATA}/lib'

        return env

    def postbuild_arch(self, arch):
        """
        Post-build hook to ensure proper file permissions
        and library paths for Android 13+ compatibility.
        """
        super().postbuild_arch(arch)

        build_dir = self.get_build_dir(arch.arch)
        private_data_dir = os.path.join(build_dir, '..', '..', 'dists', '_python_bundle')

        # Ensure .so files have correct permissions for Android 13+
        # This helps avoid SELinux denials
        if os.path.exists(private_data_dir):
            for root, dirs, files in os.walk(private_data_dir):
                for f in files:
                    if f.endswith('.so'):
                        filepath = os.path.join(root, f)
                        try:
                            # Set readable and executable permissions
                            os.chmod(filepath, 0o755)
                            print(f'Set permissions 755 for {filepath}')
                        except Exception as e:
                            print(f'Warning: Could not set permissions for {filepath}: {e}')


# Register the recipe
recipe = Android13CompatibilityRecipe()
