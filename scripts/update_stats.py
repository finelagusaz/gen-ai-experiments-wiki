#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
実験データを収集してStats.mdとグラフを自動生成するスクリプト

使い方:
    python scripts/update_stats.py
"""

import sys
import io
import re

# Windows環境での文字化け対策
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
import json
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUI不要のバックエンド

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# ディレクトリ設定
BASE_DIR = Path(__file__).parent.parent
EXPERIMENTS_DIR = BASE_DIR  # 実験ファイルはルートディレクトリに配置
IMAGES_DIR = BASE_DIR / "images"
STATS_FILE = BASE_DIR / "Stats.md"

# 画像ディレクトリを作成
IMAGES_DIR.mkdir(exist_ok=True)

# 評価記号の定義
RATING_ORDER = {"◎": 4, "○": 3, "△": 2, "❌": 1}
RATING_LABELS = {"◎": "期待以上", "○": "期待通り", "△": "期待以下", "❌": "失敗"}


def parse_experiment(file_path):
    """実験ファイルをパースして情報を抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # ファイル名からIDを取得（例: 001.md -> 001）
    data = {"id": file_path.stem}

    # タイトルからIDを抽出（ただしファイル名優先）
    title_match = re.search(r'# 実験 (.+?):', content)
    if title_match:
        title_id = title_match.group(1).strip()
        # "ID"のようなプレースホルダーでなければ使用
        if title_id and title_id != "ID":
            data["id"] = title_id

    # 基本情報抽出
    date_match = re.search(r'- 日付: (.+)', content)
    if date_match:
        data["date"] = date_match.group(1).strip()

    recorder_match = re.search(r'- 記録者: (.+)', content)
    if recorder_match:
        data["recorder"] = recorder_match.group(1).strip()

    model_match = re.search(r'- モデル: (.+)', content)
    if model_match:
        data["model"] = model_match.group(1).strip()

    target_match = re.search(r'- 対象: (.+)', content)
    if target_match:
        data["target"] = target_match.group(1).strip()

    # 評価抽出 (〇を○に正規化)
    rating_match = re.search(r'\*\*評価: ([◎○〇△❌])\*\*', content)
    if rating_match:
        rating = rating_match.group(1).strip()
        # 全角0を○に正規化
        rating = rating.replace('〇', '○')
        data["rating"] = rating

    # タグ抽出 (バッククォートとバックスラッシュエスケープ対応)
    tags_match = re.search(r'\*\*タグ:\*\*.*', content)
    if tags_match:
        tags_text = tags_match.group(0)
        # \`tag\` または `tag` の形式に対応
        data["tags"] = re.findall(r'\\?`([^`\\]+)\\?`', tags_text)
    else:
        data["tags"] = []

    return data


def collect_experiments():
    """全実験データを収集"""
    experiments = []
    # ルートディレクトリの数字で始まる.mdファイルを実験ファイルとして扱う
    for exp_file in sorted(EXPERIMENTS_DIR.glob("[0-9]*.md")):
        try:
            exp_data = parse_experiment(exp_file)
            experiments.append(exp_data)
        except Exception as e:
            print(f"警告: {exp_file.name} の解析に失敗: {e}")

    return experiments


def calculate_stats(experiments):
    """統計情報を計算"""
    total = len(experiments)

    # 評価別カウント
    rating_counts = Counter(exp.get("rating", "不明") for exp in experiments)

    # 成功率 (○以上)
    success_count = sum(rating_counts.get(r, 0) for r in ["◎", "○"])
    success_rate = (success_count / total * 100) if total > 0 else 0

    # モデル別統計
    model_stats = defaultdict(lambda: {"total": 0, "ratings": Counter()})
    for exp in experiments:
        model = exp.get("model", "不明")
        rating = exp.get("rating", "不明")
        model_stats[model]["total"] += 1
        model_stats[model]["ratings"][rating] += 1

    # タグ統計
    tag_counts = Counter()
    tag_experiments = defaultdict(list)
    for exp in experiments:
        for tag in exp.get("tags", []):
            tag_counts[tag] += 1
            tag_experiments[tag].append(exp.get("id", "不明"))

    return {
        "total": total,
        "success_rate": success_rate,
        "rating_counts": rating_counts,
        "model_stats": model_stats,
        "tag_counts": tag_counts,
        "tag_experiments": tag_experiments,
    }


def generate_timeline_chart(experiments):
    """評価推移のグラフを生成"""
    if not experiments:
        return

    # 日付順にソート
    sorted_exps = sorted(experiments, key=lambda x: x.get("date", ""))

    dates = [exp.get("id", "") for exp in sorted_exps]
    ratings = [RATING_ORDER.get(exp.get("rating", ""), 0) for exp in sorted_exps]

    plt.figure(figsize=(10, 6))
    plt.plot(dates, ratings, marker='o', linewidth=2, markersize=8)
    plt.xlabel("Experiment ID", fontsize=12)
    plt.ylabel("Rating", fontsize=12)
    plt.title("Experiment Rating Timeline", fontsize=14)
    plt.yticks([1, 2, 3, 4], ["Failed", "Below", "Met", "Exceeded"])
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "timeline.png", dpi=150, bbox_inches='tight')
    plt.close()


def generate_model_comparison_chart(model_stats):
    """モデル別比較グラフを生成"""
    if not model_stats:
        return

    models = list(model_stats.keys())
    success_rates = []

    for model in models:
        ratings = model_stats[model]["ratings"]
        total = model_stats[model]["total"]
        success = sum(ratings.get(r, 0) for r in ["◎", "○"])
        rate = (success / total * 100) if total > 0 else 0
        success_rates.append(rate)

    plt.figure(figsize=(10, 6))
    bars = plt.bar(models, success_rates, color='steelblue', alpha=0.8)
    plt.xlabel("Model", fontsize=12)
    plt.ylabel("Success Rate (%)", fontsize=12)
    plt.title("Model Comparison - Success Rate", fontsize=14)
    plt.ylim(0, 105)

    # バーの上に数値を表示
    for bar, rate in zip(bars, success_rates):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=10)

    plt.xticks(rotation=15, ha='right')
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "model_comparison.png", dpi=150, bbox_inches='tight')
    plt.close()


def generate_tag_cloud_chart(tag_counts):
    """タグ出現頻度のグラフを生成"""
    if not tag_counts:
        return

    tags = list(tag_counts.keys())
    counts = list(tag_counts.values())

    plt.figure(figsize=(10, 6))
    bars = plt.barh(tags, counts, color='coral', alpha=0.8)
    plt.xlabel("Frequency", fontsize=12)
    plt.ylabel("Tag", fontsize=12)
    plt.title("Tag Frequency", fontsize=14)

    # バーの横に数値を表示
    for bar, count in zip(bars, counts):
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2.,
                f' {count}', ha='left', va='center', fontsize=10)

    plt.grid(True, axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / "tag_cloud.png", dpi=150, bbox_inches='tight')
    plt.close()


def generate_stats_md(experiments, stats):
    """Stats.mdを生成"""
    today = datetime.now().strftime("%Y-%m-%d")

    content = f"""# 統計・分析

[[Home|← トップへ]]

最終更新: {today}

---

## サマリー

- **総実験数:** {stats['total']}
- **今週の実験数:** {stats['total']}
- **成功率 (○以上):** {stats['success_rate']:.1f}%

## 評価別内訳

| 評価 | 件数 | 割合 |
|------|------|------|
"""

    for rating in ["◎", "○", "△", "❌"]:
        count = stats['rating_counts'].get(rating, 0)
        percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
        label = RATING_LABELS[rating]
        content += f"| {rating} {label} | {count} | {percentage:.1f}% |\n"

    content += """
## モデル別統計

| モデル | 実験数 | ◎ | ○ | △ | ❌ | 成功率 |
|--------|--------|---|---|---|---|--------|
"""

    for model, data in stats['model_stats'].items():
        total = data['total']
        ratings = data['ratings']
        success = sum(ratings.get(r, 0) for r in ["◎", "○"])
        success_rate = (success / total * 100) if total > 0 else 0
        content += f"| {model} | {total} | {ratings.get('◎', 0)} | {ratings.get('○', 0)} | {ratings.get('△', 0)} | {ratings.get('❌', 0)} | {success_rate:.1f}% |\n"

    content += """
## タグ別統計

| タグ | 出現回数 | 関連実験 |
|------|----------|----------|
"""

    for tag, count in stats['tag_counts'].most_common():
        exp_links = ", ".join([f"[[{exp_id}]]" for exp_id in stats['tag_experiments'][tag]])
        content += f"| {tag} | {count} | {exp_links} |\n"

    content += """
---

## グラフ

### 評価推移
![評価推移](./images/timeline.png)

### モデル別比較
![モデル別比較](./images/model_comparison.png)

### タグクラウド
![タグクラウド](./images/tag_cloud.png)

---

**自動生成:** このページは `scripts/update_stats.py` により自動更新されます。
"""

    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    """メイン処理"""
    print("実験データを収集中...")
    experiments = collect_experiments()
    print(f"✓ {len(experiments)} 件の実験を検出")

    if not experiments:
        print("実験データが見つかりません")
        return

    print("\n統計情報を計算中...")
    stats = calculate_stats(experiments)
    print(f"✓ 成功率: {stats['success_rate']:.1f}%")

    print("\nグラフを生成中...")
    generate_timeline_chart(experiments)
    print("✓ timeline.png")

    generate_model_comparison_chart(stats['model_stats'])
    print("✓ model_comparison.png")

    generate_tag_cloud_chart(stats['tag_counts'])
    print("✓ tag_cloud.png")

    print("\nStats.mdを更新中...")
    generate_stats_md(experiments, stats)
    print("✓ Stats.md")

    print("\n完了！")


if __name__ == "__main__":
    main()
