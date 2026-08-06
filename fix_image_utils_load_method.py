import re

with open('utils/image_utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
new_lines = []
skip = False
load_image_count = 0

for i, line in enumerate(lines):
    if line.strip() == '@staticmethod' and lines[i+1].strip().startswith('def load_image'):
        load_image_count += 1
        if load_image_count < 3:
            skip = True
            continue
        elif load_image_count == 3:
            skip = False

    if skip and line.strip() == '@staticmethod' and not lines[i+1].strip().startswith('def load_image'):
        skip = False

    if not skip:
        new_lines.append(line)

new_method = """    @staticmethod
    def _load_image_cached(image_path, resize=True, return_path=False):
        active_paths_tuple = tuple(path_manager.pic_path)
        win_size = cfg.set_win_size if resize else None
        cache_key = (image_path, resize, return_path, win_size, active_paths_tuple)

        cached_result = ImageUtils._template_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            img_path = None
            selected_path = None
            for path in active_paths_tuple:
                img_path = os.path.join(f"./assets/images/{path}/{image_path}")
                if os.path.exists(img_path):
                    selected_path = path
                    break
            if img_path is None or not os.path.exists(img_path):
                log.error(f"未找到图片： {image_path} ")
                return (None, None) if return_path else None
            # 使用上下文管理器打开图片文件，确保文件对象及时关闭
            with Image.open(img_path) as img:
                image = ImageUtils._prepare_loaded_image(np.array(img), resize)
                result = (image, selected_path) if return_path else image
                ImageUtils._template_cache.put(cache_key, result)
                return result
        except FileNotFoundError:
            log.error(f"未找到图片： {image_path} ")
            return (None, None) if return_path else None
        except IOError:
            log.error(f"无法读取图片： {image_path}")
            return (None, None) if return_path else None
        except Exception as e:
            log.error(f"加载图片时发生错误： {e}")
            return (None, None) if return_path else None
"""

for i, line in enumerate(new_lines):
    if line.strip() == 'def check_default_path_exists(image_path):':
        insert_idx = i - 1
        break

final_content = '\n'.join(new_lines[:insert_idx]) + '\n' + new_method + '\n' + '\n'.join(new_lines[insert_idx:])

with open('utils/image_utils.py', 'w', encoding='utf-8') as f:
    f.write(final_content)
