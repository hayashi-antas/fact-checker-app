# Fact Checker App

Perplexity Sonar APIを使用して、主張や記事の事実確認を行うチャットアプリです。

## 機能

- **チャット形式のUI**: 直感的な対話インターフェース
- **主張のファクトチェック**: テキストを入力して即座に検証
- **URL対応**: 記事URLを入力すると自動でテキストを抽出
- **詳細な分析**: 各主張ごとの評価と説明
- **情報源の引用**: 検証に使用した情報源を表示

## なぜ Perplexity Fact Check CLI なのか

本アプリでは、Perplexity Sonar API を直接呼び出すのではなく、  
公式の **Perplexity Fact Check CLI** を内部コンポーネントとして利用しています。

Fact Check CLI は、単発の質問応答ではなく、  
**「主張単位への分解 → 自動ウェブリサーチ → 構造化された判定出力」**  
という多段ワークフローを前提に設計された、ファクトチェック専用ツールです。

内部的には、入力されたテキストや URL から文を抽出し、主張ごとに分解したうえで、  
各主張について Sonar がウェブリサーチを行い、関連ソースとエビデンスを収集します。

その結果をもとに、各主張を  
**TRUE / FALSE / MISLEADING / UNVERIFIABLE**  
のいずれかで評価し、根拠と引用 URL を含む **構造化された JSON** として返却します。

CLI 側ではこの JSON をパースし、  
- 全体評価（MOSTLY_TRUE / MIXED / MOSTLY_FALSE）
- 要約
- 主張ごとの評価一覧と根拠ソース  

を、人間可読なテキストまたは JSON 形式で出力します。

私はこの Fact Check CLI を **内部エンジンとして利用する GUI アプリ**を開発しています。  
GUI 上では、ワンクリックで

**主張単位の分解 → 自動ウェブリサーチ → 構造化された判定と根拠ソースの提示**

までを一気通貫で実行でき、  
「どの主張が、なぜ正しい／誤っているのか」を直感的に確認できる点に価値を置いています。​

## 評価の見方

### 全体評価
- 🟢 **おおむね真実** (MOSTLY_TRUE)
- 🟠 **混合** (MIXED) - 一部正確、一部不正確
- 🔴 **おおむね虚偽** (MOSTLY_FALSE)

### 各主張の評価
- ✅ **真実** (TRUE) - 事実に基づいている
- ❌ **虚偽** (FALSE) - 証拠と矛盾
- ⚠️ **誤解を招く** (MISLEADING) - 一部真実だが誤解を招く可能性
- ❓ **検証不能** (UNVERIFIABLE) - 利用可能な情報で確認できない

## ローカルでの実行

```bash
# 依存関係のインストール
pip install -r requirements.txt

# アプリの起動
streamlit run app.py
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `PPLX_API_KEY` | Perplexity APIキー |

## サンプル画面

<p align="center">
  <a href="https://gyazo.com/ccb0ce4e0528834d6fccb088c3f3adc0">
    <img src="https://i.gyazo.com/ccb0ce4e0528834d6fccb088c3f3adc0.png" />
  </a>
</p>

<p align="center">
  <a href="https://gyazo.com/b98f599991d72efbe46ea341aa13e020">
    <img src="https://i.gyazo.com/b98f599991d72efbe46ea341aa13e020.png" />
  </a>
</p>

<p align="center">
  <a href="https://gyazo.com/af1c984dca93784c8d258edc70667452">
    <img src="https://i.gyazo.com/af1c984dca93784c8d258edc70667452.png" />
  </a>
</p>


## ライセンス

MIT License

---

Based on [Perplexity API Cookbook - Fact Checker CLI](https://docs.perplexity.ai/cookbook/examples/fact-checker-cli/README)
