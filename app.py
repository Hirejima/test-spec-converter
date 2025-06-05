import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path

class SpecManager:
    def __init__(self):
        self.master_data_path = Path('master_data.json')
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize master data if not exists
        if not self.master_data_path.exists():
            self.master_data = {
                'standard_terms': {},
                'varied_terms': {}
            }
            self.save_master_data()
        else:
            self.load_master_data()

    def load_master_data(self):
        with open(self.master_data_path, 'r', encoding='utf-8') as f:
            self.master_data = json.load(f)

    def save_master_data(self):
        with open(self.master_data_path, 'w', encoding='utf-8') as f:
            json.dump(self.master_data, f, ensure_ascii=False, indent=2)

    def add_term_mapping(self, standard_term, varied_term):
        if standard_term not in self.master_data['standard_terms']:
            self.master_data['standard_terms'][standard_term] = []
        self.master_data['standard_terms'][standard_term].append(varied_term)
        self.save_master_data()

    def remove_term_mapping(self, standard_term, varied_term):
        if standard_term in self.master_data['standard_terms']:
            if varied_term in self.master_data['standard_terms'][standard_term]:
                self.master_data['standard_terms'][standard_term].remove(varied_term)
                self.save_master_data()

def main():
    st.title("試験スペック整理ツール")
    
    # サイドバーの設定
    st.sidebar.title("機能選択")
    page = st.sidebar.selectbox("機能を選択", ["マスターデータ管理", "スペック整理"])
    
    spec_manager = SpecManager()
    
    if page == "マスターデータ管理":
        st.header("マスターデータ管理")
        
        col1, col2 = st.columns(2)
        with col1:
            standard_term = st.text_input("統一用語")
        with col2:
            varied_term = st.text_input("バラバラ用語")
        
        if st.button("追加"):
            if standard_term and varied_term:
                spec_manager.add_term_mapping(standard_term, varied_term)
                st.success(f"{standard_term} - {varied_term}のマッピングを追加しました")
        
        # 既存のマッピング表示
        st.subheader("現在のマッピング")
        for std_term, varied_terms in spec_manager.master_data['standard_terms'].items():
            with st.expander(std_term):
                for varied in varied_terms:
                    st.write(varied)
                    if st.button(f"削除: {varied}", key=f"delete_{varied}"):
                        spec_manager.remove_term_mapping(std_term, varied)
                        st.success(f"{varied}のマッピングを削除しました")
    
    elif page == "スペック整理":
        st.header("スペック整理")
        
        # ファイルアップロード
        uploaded_file = st.file_uploader("スペック文書をアップロード", 
                                        type=['pdf', 'docx', 'png', 'jpg'])
        
        if uploaded_file is not None:
            # TODO: ファイル処理ロジックの実装
            st.write("アップロードされたファイル:", uploaded_file.name)
            
            if st.button("処理実行"):
                # TODO: 実際の処理ロジックの実装
                st.write("処理が実行されました")

if __name__ == "__main__":
    main()
