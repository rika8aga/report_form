import streamlit as st
from report_app.settings import user, style_to_xlsx
from report_app.levels import Levels
from report_app.filtering import by_group, by_date0
from report_app.selector import ProjectSelector, MissReports
from report_app.plots import group_chart
from report_app.to_import import cached_expenses, GroupReport, resources
from report_app.selector import Selectors

st.set_page_config(
    page_title='Отчет по отделам',
    page_icon=':triangular_ruler:',
    layout='wide'
)

st.markdown("# Отчет по отделам")

try:
    user_func = user()
    user = user_func['user']
    st.sidebar.markdown(f'### {user.name}')
    st.sidebar.markdown(f'##### {user.group}')
    user_func['form'].logout('Выйти', 'sidebar')
    match user.level:
        case Levels.leader | Levels.admin:
            match user.level:
                case Levels.admin:
                    with st.spinner('Загрузка данных'):
                        report = cached_expenses('all')
                    groups = st.selectbox(
                        'Отдел',
                        options=report['Отдел'].unique()
                    )
                    by_group = by_group(report, groups)
                case _:
                    with st.spinner('Загрузка данных'):
                        by_group = cached_expenses(f'{user.group_code}-')
                        groups = st.text_input(
                            'Отдел',
                            value=user.group,
                            disabled=True
                        )
            with st.sidebar:
                selector = Selectors()
                selector.select_date_filter(-5)
                selector.select_value_filter()
            report_selection = by_date0(by_group, selector.dates)
            tab1, tab2, tab3 = st.tabs(['По проектам', 'По сотрудникам', 'Сданы ли отчеты'])
            with tab1:
                project_selector = ProjectSelector(report_selection)
                project_selector.get_styled_pivot()
                styled_pivot = project_selector.styled_pivot
                match styled_pivot:
                    case None:
                        st.write('Нет данных')
                    case _:
                        st.table(styled_pivot)
                        st.download_button(
                            'Экспорт таблицы',
                            style_to_xlsx(styled_pivot),
                            file_name='По проектам.xlsx'
                        )
                        group_chart(project_selector.pivot)
            with tab2:
                group_report = GroupReport(report_selection)
                group_report.get_fields()
                group_report.get_pivot(selector.period, selector.value, selector.style_option)
            with tab3:
                miss_reports = MissReports(groups, report_selection, resources())
                miss_reports.pivot_to_style()
                missing_reports = miss_reports.missing_reports
                match missing_reports:
                    case None:
                        st.write('Нет данных')
                    case _:
                        st.table(missing_reports)
            if st.button('Обновить данные'):
                st.experimental_memo.clear()
                st.experimental_rerun()
        case _:
            st.warning('Доступ ограничен')
except AttributeError:
    pass
