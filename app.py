import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
import pdfplumber
from pdfminer.high_level import extract_text
import io
from datetime import datetime
import re

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

    def process_pdf(self, pdf_file):
        try:
            with pdfplumber.open(pdf_file) as pdf:
                all_data = []
                item_number = 1
                current_major = None
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # 最初の3ページはスキップ
                    if page_num <= 3:
                        continue
                    
                    text = page.extract_text()
                    if text:
                        lines = text.split('\n')
                        
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # 大項目の検出 (■で始まり、表番号を含まない)
                            if line.startswith('■') and not any(f"表{i}" in line for i in range(1, 100)):
                                current_major = line
                                # 大項目行を追加
                                all_data.append({
                                    '項番': item_number,
                                    '大項目': current_major,
                                    '小項目': '',
                                    '試験内容': '',
                                    '試験条件': '',
                                    '判定要領': ''
                                })
                                item_number += 1
                                continue
                            
                            # 表タイトルのスキップ
                            if any(f"表{i}" in line for i in range(1, 100)):
                                continue
                            
                            # 1-1形式の数字で始まる行は試験内容
                            if re.match(r'^\d+-\d+', line):
                                all_data.append({
                                    '項番': item_number,
                                    '大項目': current_major if current_major else '',
                                    '小項目': '',
                                    '試験内容': line,
                                    '試験条件': '',
                                    '判定要領': ''
                                })
                                item_number += 1
                                continue
                            
                            # 試験条件の抽出
                            if "試験条件" in line or "試験方法" in line or "試験項目" in line:
                                # キーワード以降のテキストを抽出
                                condition_text = re.split(r'試験条件|試験方法|試験項目', line, maxsplit=1)[-1].strip()
                                # 要約（最初の句点まで）
                                if '。' in condition_text:
                                    condition_text = condition_text.split('。', 1)[0] + '。'
                                
                                # 直前の行に追加
                                if all_data:
                                    all_data[-1]['試験条件'] = condition_text
                                continue
                            
                            # 判定要領の抽出
                            if "確認項目" in line or "判定" in line:
                                # キーワード以降のテキストを抽出
                                criteria_text = re.split(r'確認項目|判定', line, maxsplit=1)[-1].strip()
                                # 要約（最初の句点まで）
                                if '。' in criteria_text:
                                    criteria_text = criteria_text.split('。', 1)[0] + '。'
                                
                                # 直前の行に追加
                                if all_data:
                                    all_data[-1]['判定要領'] = criteria_text
                                continue
                            
                            # その他の行は試験内容として追加
                            all_data.append({
                                '項番': item_number,
                                '大項目': current_major if current_major else '',
                                '小項目': '',
                                '試験内容': line,
                                '試験条件': '',
                                '判定要領': ''
                            })
                            item_number += 1
                
                return pd.DataFrame(all_data)
        except Exception as e:
            st.error(f"PDF処理中にエラーが発生しました: {str(e)}")
            return None

def main():
    st.title("試験スペック整理ツール")
    
    # サイドバーの設定
    st.sidebar.title("機能選択")
    page = st.sidebar.selectbox("機能を選択", ["マスターデータ管理", "スペック整理"])
    
    spec_manager = SpecManager()
    
    if page == "マスターデータ管理":
        st.header("マスターデータ管理")
        
        # マスターデータの表示
        if spec_manager.master_data['standard_terms']:
            st.subheader("現在のマスターデータ")
            for std_term, varied_terms in spec_manager.master_data['standard_terms'].items():
                with st.expander(f"統一用語: {std_term}"):
                    for varied in varied_terms:
                        st.write(f"- {varied}")
        else:
            st.warning("マスターデータが設定されていません。")
            
        # マスターデータの追加フォーム
        st.subheader("新しいマッピングの追加")
        col1, col2 = st.columns(2)
        with col1:
            standard_term = st.text_input("統一用語", placeholder="例：ブレーキ試験")
        with col2:
            varied_term = st.text_input("バラバラ用語", placeholder="例：ブレーキ性能試験, ブレーキ機能試験")
        
        if st.button("追加"):
            if standard_term and varied_term:
                spec_manager.add_term_mapping(standard_term, varied_term)
                st.success(f"{standard_term} - {varied_term}のマッピングを追加しました")
            else:
                st.warning("統一用語とバラバラ用語の両方を入力してください")
        
        # マスターデータの編集
        st.subheader("マッピングの編集")
        if spec_manager.master_data['standard_terms']:
            selected_std_term = st.selectbox("編集する統一用語を選択", 
                                           list(spec_manager.master_data['standard_terms'].keys()))
            if selected_std_term:
                varied_terms = spec_manager.master_data['standard_terms'][selected_std_term]
                
                col1, col2 = st.columns(2)
                with col1:
                    new_varied = st.text_input("追加するバラバラ用語")
                    if st.button("追加"):
                        if new_varied:
                            spec_manager.add_term_mapping(selected_std_term, new_varied)
                            st.success(f"{new_varied}を追加しました")
                
                with col2:
                    if varied_terms:
                        selected_varied = st.selectbox("削除するバラバラ用語を選択", varied_terms)
                        if st.button("削除"):
                            spec_manager.remove_term_mapping(selected_std_term, selected_varied)
                            st.success(f"{selected_varied}を削除しました")
                    else:
                        st.write("バラバラ用語が設定されていません")
    
    elif page == "スペック整理":
        st.header("スペック整理")
        
        # ファイルアップロード
        uploaded_file = st.file_uploader("スペック文書をアップロード", 
                                        type=['pdf', 'docx', 'png', 'jpg'])
        
        if uploaded_file is not None:
            # ファイルを保存
            file_path = os.path.join('temp', uploaded_file.name)
            os.makedirs('temp', exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
        
            if st.button("処理実行"):
                try:
                    # PDF処理
                    df = spec_manager.process_pdf(file_path)
                    
                    if df is not None:
                        # Excelファイル名の生成
                        excel_file = os.path.join('output', f"{os.path.splitext(uploaded_file.name)[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                        
                        # Excelに保存
                        df.to_excel(excel_file, index=False)
                        st.success(f"Excelファイルが生成されました: {excel_file}")
                        
                        # ダウンロードリンクの生成
                        with open(excel_file, 'rb') as f:
                            st.download_button(
                                label="Excelファイルをダウンロード",
                                data=f,
                                file_name=os.path.basename(excel_file),
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                except Exception as e:
                    st.error(f"処理中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()
