# 生成AI×創作 実験ログ

生成AIを使った創作実験の記録と分析を行うWikiです。

## 📊 [実験一覧](./Home.md)

すべての実験記録を一覧で確認できます。

## 📈 [統計・分析](./Stats.md)

実験データの統計情報とグラフを確認できます。

## 🔧 使い方

### 新しい実験を記録する

1. VSCodeで新しいMarkdownファイルを作成（例: `002.md`）
2. `exp` + Tab でテンプレートを展開
3. 実験内容を記入
4. `Home.md` に `row` + Tab で一覧に追加

### 統計を更新する

```bash
python scripts/update_stats.py
```

これにより以下が自動生成されます:
- `Stats.md` - 統計情報
- `images/timeline.png` - 評価推移グラフ
- `images/model_comparison.png` - モデル別比較グラフ
- `images/tag_cloud.png` - タグ頻度グラフ

## 📁 ファイル構造

```
.
├── Home.md              # トップページ
├── Stats.md             # 統計ページ（自動生成）
├── 001.md, 002.md...    # 各実験の詳細
├── images/              # グラフ画像
├── scripts/             # 統計生成スクリプト
└── templates/           # テンプレートファイル
```

## 🎨 評価記号

- ◎ 期待以上
- ○ 期待通り
- △ 期待以下
- ❌ 失敗

---

**GitHub Pages URL:** https://finelagusaz.github.io/gen-ai-experiments-wiki/
