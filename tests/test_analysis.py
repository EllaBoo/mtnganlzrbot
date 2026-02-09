"""
Tests for core/analysis.py

Covers:
- detect_domain_by_keywords (synchronous, no API needed)
"""
import pytest

from core.analysis import detect_domain_by_keywords


class TestDetectDomainByKeywords:
    def test_marketing_keywords(self):
        text = "Нам нужно усилить маркетинг и запустить рекламу. Конверсия очень низкая."
        assert detect_domain_by_keywords(text) == "marketing"

    def test_sales_keywords(self):
        text = "Продажи упали. Нужно улучшить CRM и pipeline. Клиент ждёт сделку."
        assert detect_domain_by_keywords(text) == "sales"

    def test_development_keywords(self):
        text = "В текущем sprint мы работаем над backend API. Есть баги после релиза."
        assert detect_domain_by_keywords(text) == "development"

    def test_product_keywords(self):
        text = "Нужно обновить roadmap продукта и приоритизировать backlog. MVP готов."
        assert detect_domain_by_keywords(text) == "product"

    def test_hr_keywords(self):
        text = "Собеседование кандидата прошло хорошо. Онбординг нового сотрудника."
        assert detect_domain_by_keywords(text) == "hr"

    def test_finance_keywords(self):
        text = "Бюджет на Q2 утверждён. Выручка растёт, cash flow стабилен."
        assert detect_domain_by_keywords(text) == "finance"

    def test_strategy_keywords(self):
        text = "Нужно пересмотреть стратегию. OKR на следующий квартал. Конкуренты активны."
        assert detect_domain_by_keywords(text) == "strategy"

    def test_management_keywords(self):
        text = "Управление командой требует делегирования. Leadership важен."
        assert detect_domain_by_keywords(text) == "management"

    def test_data_keywords(self):
        text = "Дашборд с метриками готов. SQL-запросы оптимизированы. Аналитика показывает рост."
        assert detect_domain_by_keywords(text) == "data"

    def test_legal_keywords(self):
        text = "Договор с поставщиком подписан. Юридический отдел проверил compliance."
        assert detect_domain_by_keywords(text) == "legal"

    def test_design_keywords(self):
        text = "Новый дизайн интерфейса в Figma. UX-исследование завершено."
        assert detect_domain_by_keywords(text) == "design"

    def test_medicine_keywords(self):
        text = "Пациент жалуется на симптомы. Врач поставил диагноз и назначил лечение."
        assert detect_domain_by_keywords(text) == "medicine"

    def test_education_keywords(self):
        text = "Новый курс для студентов. Преподаватель подготовил лекцию по образованию."
        assert detect_domain_by_keywords(text) == "education"

    def test_no_keywords_returns_general(self):
        text = "Just a regular conversation about nothing in particular."
        assert detect_domain_by_keywords(text) == "general"

    def test_empty_text_returns_general(self):
        assert detect_domain_by_keywords("") == "general"

    def test_case_insensitive(self):
        text = "МАРКЕТИНГ и РЕКЛАМА в нашей компании"
        assert detect_domain_by_keywords(text) == "marketing"

    def test_english_keywords_work(self):
        text = "Our marketing brand strategy needs more advertising and SEO work."
        assert detect_domain_by_keywords(text) == "marketing"

    def test_mixed_domain_highest_score_wins(self):
        """When multiple domains match, the one with most keyword hits wins."""
        text = "маркетинг реклама бренд контент smm seo. одна продажа."
        result = detect_domain_by_keywords(text)
        assert result == "marketing"
