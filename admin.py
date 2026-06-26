# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# === НАСТРОЙКИ СТРАНИЦЫ ===
st.set_page_config(
    page_title="LeadCatcher — Панель управления",
    page_icon="🎯",
    layout="wide"
)

# === ЗАГОЛОВОК ===
st.title("🎯 LeadCatcher")
st.markdown("### Панель управления заявками")
st.markdown("---")

# === ПОДКЛЮЧЕНИЕ К БД ===
@st.cache_data
def get_leads():
    """Получает все заявки из базы данных."""
    try:
        conn = sqlite3.connect("leads.db")
        df = pd.read_sql("SELECT * FROM leads ORDER BY id DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Ошибка подключения к базе: {e}")
        return pd.DataFrame()

# === ПОЛУЧАЕМ ДАННЫЕ ===
df = get_leads()

# === СТАТИСТИКА ===
if not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Всего заявок", len(df))
    
    with col2:
        today = datetime.now().strftime('%Y-%m-%d')
        today_count = len(df[df['created_at'].str.contains(today)])
        st.metric("📅 Сегодня", today_count)
    
    with col3:
        st.metric("📡 Источников", df['source'].nunique())
    
    with col4:
        unique_contacts = df['contact'].nunique()
        st.metric("👥 Уникальных контактов", unique_contacts)
    
    st.markdown("---")
    
    # === ФИЛЬТРЫ ===
    col1, col2 = st.columns(2)
    
    with col1:
        sources = ['Все'] + list(df['source'].unique())
        selected_source = st.selectbox("📡 Источник:", sources)
    
    with col2:
        search_term = st.text_input("🔍 Поиск по имени или контакту:")
    
    # === ПРИМЕНЯЕМ ФИЛЬТРЫ ===
    filtered_df = df.copy()
    
    if selected_source != 'Все':
        filtered_df = filtered_df[filtered_df['source'] == selected_source]
    
    if search_term:
        filtered_df = filtered_df[
            (filtered_df['name'].str.contains(search_term, case=False)) |
            (filtered_df['contact'].str.contains(search_term, case=False))
        ]
    
    # === ПОКАЗЫВАЕМ ТАБЛИЦУ ===
    st.markdown(f"### 📋 Заявок найдено: {len(filtered_df)}")
    
    if not filtered_df.empty:
        # Переименовываем колонки для красоты
        display_df = filtered_df.copy()
        display_df = display_df.rename(columns={
            'id': 'ID',
            'created_at': 'Дата и время',
            'name': 'Имя',
            'contact': 'Контакт',
            'source': 'Источник',
            'comment': 'Комментарий'
        })
        
        # Показываем таблицу
        st.dataframe(
            display_df[['ID', 'Дата и время', 'Имя', 'Контакт', 'Источник', 'Комментарий']],
            use_container_width=True,
            hide_index=True
        )
        
        # === ЭКСПОРТ В CSV ===
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            # Конвертируем в CSV
            csv_buffer = io.StringIO()
            filtered_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_bytes = csv_buffer.getvalue().encode('utf-8')
            
            st.download_button(
                label="📥 Скачать CSV",
                data=csv_bytes,
                file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            if st.button("🔄 Обновить данные"):
                st.cache_data.clear()
                st.rerun()
    
    else:
        st.warning("⚠️ По вашему запросу ничего не найдено")
    
    # === ИНФОРМАЦИЯ ОБ ИСТОЧНИКАХ ===
    st.markdown("---")
    st.markdown("### 📊 Распределение по источникам")
    
    source_counts = df['source'].value_counts()
    st.bar_chart(source_counts)
    
else:
    st.info("📭 Пока нет заявок. Отправьте первую заявку через API!")
    st.code("""
    # Пример отправки заявки:
    curl -X POST http://127.0.0.1:8000/lead \\
      -H "Content-Type: application/json" \\
      -d '{
        "name": "Ирина",
        "contact": "+79990000000",
        "source": "landing",
        "comment": "Хочу консультацию"
      }'
    """)

# === ПОДВАЛ ===
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    LeadCatcher v1.0.0 | Автоматический сбор заявок
</div>
""", unsafe_allow_html=True)