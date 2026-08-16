import re

with open('utils/image_utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the body of match_template_with_multiple_targets

import ast

def replace_method():
    lines = content.split('\n')
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if 'def match_template_with_multiple_targets(screenshot, template, threshold, min_dist=10):' in line:
            start_idx = i
            break

    if start_idx != -1:
        for i in range(start_idx + 1, len(lines)):
            if lines[i].strip().startswith('def get_image_info') or (lines[i].strip().startswith('@staticmethod') and 'def get_image_info' in lines[i+1]):
                end_idx = i
                break

        if lines[end_idx].strip().startswith('@staticmethod'):
            end_idx -= 1
        else:
            while lines[end_idx-1].strip() == '':
                end_idx -= 1

        new_func = """    @staticmethod
    def match_template_with_multiple_targets(screenshot, template, threshold, min_dist=10):
        # 获取模板的宽度和高度
        w, h = ImageUtils.get_image_info(template)
        # 使用matchTemplate对图片进行模板匹配
        res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

        # 遍历所有超过阈值的区域
        loc_y, loc_x = np.where(res >= threshold)
        if len(loc_y) == 0:
            log.debug(f"未找到匹配项，最高匹配度为：{np.max(res)}")
            return []

        # 使用向量化 argsort 替代 Python 的 sorted 和 lambda，大幅提升多目标匹配的性能
        scores = res[loc_y, loc_x]
        sort_idx = np.argsort(scores)[::-1]

        # 提取排序后的坐标
        x_sorted = loc_x[sort_idx]
        y_sorted = loc_y[sort_idx]

        center_points = []
        min_dist_sq = min_dist**2

        # 遍历排序后的匹配位置
        for i in range(len(x_sorted)):
            pt_x = x_sorted[i]
            pt_y = y_sorted[i]

            # 检查当前匹配点是否与已保留的匹配点太近
            keep = True
            for kept_pt in center_points:
                if (pt_x - kept_pt[0]) ** 2 + (pt_y - kept_pt[1]) ** 2 <= min_dist_sq:
                    keep = False
                    break
            if keep:
                # 如果没有太近的匹配点，保留当前匹配点
                center_points.append((pt_x, pt_y))

        # 计算每个匹配点的中心坐标
        center_points = [(int(pt[0] + w / 2), int(pt[1] + h / 2)) for pt in center_points]
        return center_points
"""

        with open('utils/image_utils.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines[:start_idx-1]) + '\n' + new_func + '\n' + '\n'.join(lines[end_idx+1:]))

replace_method()
