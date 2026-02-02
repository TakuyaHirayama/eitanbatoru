# Focus Enemy

「苦手な英単語」が強敵として出現する、RPG風・集中学習クイズアプリ。

## 🚀 アプリ試用URL
[ここにあなたのアプリのURLを貼る]

## ✨ 特徴（独自性）
1. **忘却曲線への挑戦**: 
   Supabaseに保存された「ミス回数(miss_count)」をリアルタイムで参照。間違えれば間違えるほど、その単語がクイズに高確率で出現する「苦手集中型」のロジックを搭載しています。
2. **ゲーム要素**: 
   単語を敵に見立て、正解することでHPを削る演出を採用。学習を「作業」から「攻略」に変えます。
3. **外部API活用**: 
   Google Fonts APIを動的に読み込み、ゲームの世界観に合わせたUIデザインを実現しました。

## 🛠 使用技術
- **Frontend**: React
- **Backend/Database**: Supabase
- **External API**: Google Fonts API (デザイン最適化)

## 🏗 Database Schema (Supabase)
`words` テーブルを以下のように構成しています：
- `word` (text): 英単語
- `meaning` (text): 和訳
- `correct_count` (int): 正解数
- `miss_count` (int): ミス数（この値が大きいほど優先的に出題）
