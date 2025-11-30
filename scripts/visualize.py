#!/usr/bin/env python3
import glob
import re
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from collections import defaultdict

def parse_experiments():
    """experiments/*.md を解析"""
    data = []
    
    for filepath in glob.glob("experiments/*.md"):
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
            
            # 基本情報抽出
            date_match = re.search(r'日付: (\d{4}-\d{2}-\d{2})', content)
            model_match = re.search(r'モデル: (.+)', content)
            rating_match = re.search(r'評価: (.+)', content)
            
            if all([date_match, model_match, rating_match]):
                data.append({
                    'date': datetime.strptime(date_match.group(1), '%Y-%m-%d'),
                    'model': model_match.group(1).strip(),
                    'rating': rating_match.group(1).strip(),
                    'success': rating_match.group(1).strip() in ['○', '◎']
                })
    
    return sorted(data, key=lambda x: x['date'])

def plot_timeline(data):
    """時系列グラフ"""
    dates = [d['date'] for d in data]
    
    # 累積成功率
    cumulative_success = []
    total = 0
    success = 0
    
    for d in data:
        total += 1
        if d['success']:
            success += 1
        cumulative_success.append(success / total * 100)
    
    plt.figure(figsize=(12, 6))
    plt.plot(dates, cumulative_success, marker='o', linewidth=2)
    plt.title('Cumulative Success Rate Over Time', fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Success Rate (%)')
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig('images/timeline.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ timeline.png generated")

def plot_model_comparison(data):
    """モデル別比較"""
    models = defaultdict(lambda: {'total': 0, 'success': 0})
    
    for d in data:
        model = d['model']
        models[model]['total'] += 1
        if d['success']:
            models[model]['success'] += 1
    
    # 成功率計算
    model_names = []
    success_rates = []
    
    for model, stats in sorted(models.items()):
        if stats['total'] >= 2:  # 2件以上のみ
            model_names.append(model)
            success_rates.append(stats['success'] / stats['total'] * 100)
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(model_names, success_rates, color=['#3498db', '#e74c3c', '#2ecc71'])
    plt.title('Success Rate by Model', fontsize=14, fontweight='bold')
    plt.ylabel('Success Rate (%)')
    plt.ylim(0, 100)
    
    # 値を表示
    for bar, rate in zip(bars, success_rates):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.0f}%',
                ha='center', va='bottom')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('images/model_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ model_comparison.png generated")

if __name__ == '__main__':
    data = parse_experiments()
    
    if not data:
        print("No experiments found")
        exit(1)
    
    import os
    os.makedirs('images', exist_ok=True)
    
    plot_timeline(data)
    plot_model_comparison(data)
    
    print(f"\n✓ Analyzed {len(data)} experiments")
    print("✓ Graphs saved to images/")