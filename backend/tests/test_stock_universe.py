"""驗證 stock_universe 解析三份 txt 的正確性。"""
import pytest

from app.services.stock_universe import load_universe, get_universe


@pytest.fixture(autouse=True)
def loaded():
    load_universe()


def test_total_count():
    universe = get_universe()
    # 上市+上櫃+ETF 合計應超過 2000 檔
    assert len(universe) > 2000, f"實際載入 {len(universe)} 檔，預期 > 2000"


def test_tsmc_exists():
    universe = get_universe()
    assert "2330" in universe
    assert universe["2330"]["name"] == "台積電"
    assert universe["2330"]["market"] == "TSE"
    assert universe["2330"]["is_etf"] is False


def test_0050_exists():
    universe = get_universe()
    assert "0050" in universe
    assert universe["0050"]["name"] == "元大台灣50"
    assert universe["0050"]["is_etf"] is True
    assert universe["0050"]["industry"] == "ETF"


def test_otc_stock_exists():
    """上櫃股應歸類為 OTC。"""
    universe = get_universe()
    otc_stocks = [c for c, i in universe.items() if i["market"] == "OTC"]
    assert len(otc_stocks) > 500, f"OTC 股票數 {len(otc_stocks)} 低於預期"


def test_no_empty_name():
    universe = get_universe()
    empty_name = [code for code, info in universe.items() if not info["name"]]
    assert empty_name == [], f"發現空名稱代號：{empty_name[:5]}"


def test_industry_not_empty():
    """每檔股票都應有產業別（ETF 預設為 'ETF'，其他預設為 '其他'）。"""
    universe = get_universe()
    empty_industry = [code for code, info in universe.items() if not info["industry"]]
    assert empty_industry == [], f"發現空產業別代號：{empty_industry[:5]}"
