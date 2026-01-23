"""
Fact Checker - Streamlit Chat App
Perplexity Sonar APIを使用してファクトチェックを行うチャットアプリ
"""

import os
import re
import streamlit as st
from fact_checker import FactChecker, FactCheckResult
import requests
from newspaper import Article, ArticleException


# ページ設定
st.set_page_config(
    page_title="Fact Checker",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .rating-true { color: #28a745; font-weight: bold; }
    .rating-false { color: #dc3545; font-weight: bold; }
    .rating-misleading { color: #ffc107; font-weight: bold; }
    .rating-unverifiable { color: #6c757d; font-weight: bold; }
    .overall-mostly-true { background-color: #d4edda; padding: 10px; border-radius: 5px; }
    .overall-mixed { background-color: #fff3cd; padding: 10px; border-radius: 5px; }
    .overall-mostly-false { background-color: #f8d7da; padding: 10px; border-radius: 5px; }
    .source-link { font-size: 0.85em; color: #6c757d; }
</style>
""", unsafe_allow_html=True)


def get_api_key() -> str:
    """APIキーを取得する（環境変数 > Secrets > セッション入力）"""
    # 環境変数から取得
    api_key = os.environ.get("PPLX_API_KEY", "")
    if api_key:
        return api_key
    
    # Streamlit Secretsから取得（Hugging Face Spaces / Streamlit Cloud用）
    try:
        api_key = st.secrets.get("PPLX_API_KEY", "")
        if api_key:
            return api_key
    except Exception:
        pass
    
    # セッションステートから取得（ユーザー入力）
    return st.session_state.get("api_key", "")


def extract_text_from_url(url: str) -> str:
    """URLから記事テキストを抽出"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        article = Article(url=url)
        article.download(input_html=response.text)
        article.parse()
        
        if not article.text:
            return None
        return article.text
    except Exception as e:
        st.error(f"URLからの取得に失敗しました: {e}")
        return None


def format_result_as_markdown(result: dict) -> str:
    """ファクトチェック結果をMarkdown形式にフォーマット"""
    if "error" in result:
        return f"❌ **エラー**: {result['error']}"
    
    output = []
    
    # citations リストを取得（参照番号→URL変換用）
    citation_list = result.get("citations", [])
    
    # 各claimのsourcesを実際のURLに変換
    if citation_list and "claims" in result:
        for claim in result["claims"]:
            updated_sources = []
            for source in claim.get("sources", []):
                # 整数の場合（例: 1, 2, 3）
                if isinstance(source, int):
                    idx = source - 1
                    if 0 <= idx < len(citation_list):
                        updated_sources.append(citation_list[idx])
                    else:
                        updated_sources.append(f"[{source}]")
                # 文字列の場合
                elif isinstance(source, str):
                    # [1], [2] などの参照番号を検出
                    m = re.match(r"\[(\d+)\]", source.strip())
                    if m:
                        idx = int(m.group(1)) - 1
                        if 0 <= idx < len(citation_list):
                            updated_sources.append(citation_list[idx])
                        else:
                            updated_sources.append(source)
                    else:
                        updated_sources.append(source)
                else:
                    updated_sources.append(str(source))
            claim["sources"] = updated_sources
    
    # 全体評価
    if "overall_rating" in result:
        rating = result["overall_rating"]
        if rating == "MOSTLY_TRUE":
            emoji = "🟢"
            label = "おおむね真実"
        elif rating == "MIXED":
            emoji = "🟠"
            label = "混合"
        else:
            emoji = "🔴"
            label = "おおむね虚偽"
        
        output.append(f"## {emoji} 全体評価: {label}")
    
    # サマリー
    if "summary" in result:
        output.append(f"\n**📝 要約**\n\n{result['summary']}")
    
    # 各主張の分析
    if "claims" in result:
        output.append("\n---\n## 🔍 主張の分析\n")
        
        for i, claim in enumerate(result["claims"], 1):
            rating = claim.get("rating", "UNKNOWN")
            
            if rating == "TRUE":
                emoji = "✅"
                label = "真実"
            elif rating == "FALSE":
                emoji = "❌"
                label = "虚偽"
            elif rating == "MISLEADING":
                emoji = "⚠️"
                label = "誤解を招く"
            elif rating == "UNVERIFIABLE":
                emoji = "❓"
                label = "検証不能"
            else:
                emoji = "🔄"
                label = rating
            
            output.append(f"### 主張 {i}: {emoji} {label}")
            output.append(f"> {claim.get('claim', '主張なし')}")
            output.append(f"\n**説明**: {claim.get('explanation', '説明なし')}")
            
            # ソース
            sources = claim.get("sources", [])
            if sources:
                output.append("\n**情報源**:")
                for source in sources:
                    # URLの場合はリンクにする
                    if source.startswith("http"):
                        output.append(f"- [{source}]({source})")
                    else:
                        output.append(f"- {source}")
            output.append("")
    
    # 引用（APIからの引用がある場合）
    if "citations" in result and result["citations"]:
        output.append("\n---\n### 📚 参考文献")
        for citation in result["citations"]:
            if citation.startswith("http"):
                output.append(f"- [{citation}]({citation})")
            else:
                output.append(f"- {citation}")
    
    # raw_responseの場合
    if "raw_response" in result and "overall_rating" not in result:
        output.append("**回答**:\n")
        output.append(result["raw_response"])
    
    return "\n".join(output)


def main():
    st.title("🔍 Fact Checker")
    st.caption("Perplexity Sonar APIを使用したファクトチェックアプリ")
    
    # サイドバー設定
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # APIキー入力（環境変数にない場合のみ表示）
        env_api_key = os.environ.get("PPLX_API_KEY", "")
        secrets_api_key = ""
        try:
            secrets_api_key = st.secrets.get("PPLX_API_KEY", "")
        except Exception:
            pass
        
        if not env_api_key and not secrets_api_key:
            api_key_input = st.text_input(
                "Perplexity APIキー",
                type="password",
                value=st.session_state.get("api_key", ""),
                help="APIキーを入力してください"
            )
            if api_key_input:
                st.session_state.api_key = api_key_input
        else:
            st.success("✅ APIキー設定済み")
        
        st.divider()
        
        # モデル選択
        model = st.selectbox(
            "モデル",
            ["sonar", "sonar-pro", "sonar-reasoning", "sonar-reasoning-pro"],
            index=1,
            help="使用するPerplexityモデルを選択"
        )
        
        # 構造化出力オプション
        use_structured = st.checkbox(
            "構造化出力を使用",
            value=False,
            help="Tier 3以上のアカウントで利用可能"
        )
        
        st.divider()
        
        # 使い方
        with st.expander("📖 使い方"):
            st.markdown("""
            1. チェックしたい主張やテキストを入力
            2. URLを入力すると記事を自動取得
            3. 送信ボタンを押してファクトチェック
            
            **評価の意味**:
            - 🟢 おおむね真実
            - 🟠 混合（一部正確、一部不正確）
            - 🔴 おおむね虚偽
            
            **各主張の評価**:
            - ✅ 真実
            - ❌ 虚偽
            - ⚠️ 誤解を招く
            - ❓ 検証不能
            """)
        
        # クリアボタン
        if st.button("🗑️ 会話をクリア", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # チャット履歴の初期化
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # チャット履歴の表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # ユーザー入力
    if prompt := st.chat_input("ファクトチェックしたい内容を入力してください..."):
        # APIキーの確認
        api_key = get_api_key()
        if not api_key:
            st.error("⚠️ APIキーを設定してください（サイドバーから入力）")
            return
        
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # アシスタントの応答
        with st.chat_message("assistant"):
            with st.spinner("ファクトチェック中..."):
                try:
                    # URLかどうかを判定
                    text_to_check = prompt
                    if prompt.startswith("http://") or prompt.startswith("https://"):
                        st.info(f"📰 URLから記事を取得中: {prompt}")
                        extracted_text = extract_text_from_url(prompt)
                        if extracted_text:
                            text_to_check = extracted_text
                            st.success("記事を取得しました")
                        else:
                            st.warning("記事の取得に失敗しました。URLをそのままチェックします。")
                    
                    # FactCheckerを初期化
                    checker = FactChecker(api_key=api_key)
                    
                    # ファクトチェック実行
                    result = checker.check_claim(
                        text_to_check,
                        model=model,
                        use_structured_output=use_structured
                    )
                    
                    # 結果をフォーマット
                    formatted_result = format_result_as_markdown(result)
                    
                    # 表示
                    st.markdown(formatted_result)
                    
                    # 履歴に追加
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": formatted_result
                    })
                    
                except ValueError as e:
                    error_msg = f"❌ エラー: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                except Exception as e:
                    error_msg = f"❌ 予期しないエラーが発生しました: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })


if __name__ == "__main__":
    main()
