"""固收+ 风险视图测试。

不依赖行情源，全部指标只从 CSV 已有字段派生（到期时间/滚动/起始日/收益/复利年化/平台）。
测试用合成 InvestmentProduct，不读 data/real/ 下的真实持仓（那是 gitignore 的私人数据）。
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from asset_lens.analysis.fixed_income_risk import (
    FIXED_INCOME_TYPES,
    build_fixed_income_risk_view,
    parse_maturity_raw,
)

TODAY = date(2026, 10, 1)


def mk(
    name: str,
    amount: str = "10000",
    itype="债券",
    maturity: date | None = None,
    rolling: bool = False,
    start: date | None = None,
    annual: str | None = None,
    compound: str | None = None,
    days: int | None = None,
    platforms: dict | None = None,
):
    from asset_lens.data.models import InvestmentProduct, InvestmentType, RiskLevel

    return InvestmentProduct(
        investment_type=InvestmentType(itype),
        name=name,
        risk_level=RiskLevel.LOW,
        platform_amounts={k: Decimal(v) for k, v in (platforms or {}).items()},
        maturity_date=maturity,
        is_rolling=rolling,
        start_date=start,
        investment_days=days,
        return_rate=None,
        annual_return=Decimal(annual) if annual is not None else None,
        compound_return=Decimal(compound) if compound is not None else None,
        initial_amount=Decimal(amount),
        current_amount=Decimal(amount),
    )


# --------------------------------------------------------------------------
# 到期时间脏值解析
# --------------------------------------------------------------------------
class TestParseMaturityRaw:
    def test_parses_slash_format(self):
        """CSV 实际用的是 2026/05/25 斜杠格式。"""
        r = parse_maturity_raw("2026/05/25")
        assert r.status == "dated"
        assert r.maturity == date(2026, 5, 25)

    def test_parses_dash_format(self):
        r = parse_maturity_raw("2027-12-13")
        assert r.status == "dated"
        assert r.maturity == date(2027, 12, 13)

    def test_open_ended_sentinel(self):
        """『可赎』是开放型哨兵值，不是日期——必须和『无到期日』区分开。"""
        r = parse_maturity_raw("可赎")
        assert r.status == "open_ended"
        assert r.maturity is None

    def test_dirty_value_is_not_a_date(self):
        """实测 CSV 里出现过把基金代码 2938146 填进『到期时间』的脏值。

        若按数字当日期解析会得到 1902 年，从而把产品误判成逾期 40000 天。
        """
        r = parse_maturity_raw("2938146")
        assert r.status == "dirty"
        assert r.maturity is None

    def test_blank_is_missing(self):
        assert parse_maturity_raw("").status == "missing"
        assert parse_maturity_raw("   ").status == "missing"

    def test_none_is_missing(self):
        assert parse_maturity_raw(None).status == "missing"

    @pytest.mark.parametrize("raw", ["2026/13/45", "not-a-date", "2026-02-30", "99/99/99"])
    def test_unparseable_garbage_is_dirty(self, raw):
        """非法日期（13 月 45 日 / 2 月 30 日）不能当成有效日期。"""
        r = parse_maturity_raw(raw)
        assert r.status in {"dirty", "missing"}
        assert r.maturity is None


# --------------------------------------------------------------------------
# 到期梯队
# --------------------------------------------------------------------------
class TestMaturityLadder:
    def test_buckets_by_days_to_maturity(self):
        products = [
            mk("已到期", maturity=TODAY - timedelta(days=10)),
            mk("30天内", maturity=TODAY + timedelta(days=15)),
            mk("90天内", maturity=TODAY + timedelta(days=60)),
            mk("180天内", maturity=TODAY + timedelta(days=120)),
            mk("1年内", maturity=TODAY + timedelta(days=300)),
            mk("1年以上", maturity=TODAY + timedelta(days=500)),
        ]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        got = {b.key: b.amount for b in view.ladder.buckets}
        assert got["overdue"] == Decimal(10000)
        assert got["d30"] == Decimal(10000)
        assert got["d90"] == Decimal(10000)
        assert got["d180"] == Decimal(10000)
        assert got["d365"] == Decimal(10000)
        assert got["beyond"] == Decimal(10000)

    def test_overdue_amount_is_surfaced(self):
        """23% 的固收金额挂着过期到期日是最高优先级信号，必须单独成桶。"""
        products = [
            mk("A", amount="100000", maturity=TODAY - timedelta(days=120)),
            mk("B", amount="300000", maturity=TODAY + timedelta(days=200)),
        ]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        assert view.ladder.overdue_amount == Decimal(100000)
        assert view.ladder.overdue_count == 1
        assert view.ladder.overdue_share == pytest.approx(0.25, abs=1e-6)

    def test_open_ended_separate_from_missing(self):
        """开放型(可赎) 和 没填到期日 是两种不同风险，不该混在一个桶。"""
        products = [mk("可赎的", maturity=None), mk("没填的", maturity=None)]
        products[0].maturity_date = None
        view = build_fixed_income_risk_view(products, as_of=TODAY, raw_maturity={"可赎的": "可赎"})
        buckets = {b.key: b.amount for b in view.ladder.buckets}
        assert buckets["open_ended"] == Decimal(10000)
        assert buckets["no_maturity"] == Decimal(10000)

    def test_dirty_maturity_counted_and_reported(self):
        products = [mk("脏的", maturity=None)]
        view = build_fixed_income_risk_view(products, as_of=TODAY, raw_maturity={"脏的": "2938146"})
        assert view.ladder.dirty_count == 1
        assert view.ladder.dirty_amount == Decimal(10000)

    def test_boundary_days_are_inclusive(self):
        """d30 含第 30 天，d90 含第 90 天——边界不能漏。"""
        products = [mk("正好30", maturity=TODAY + timedelta(days=30))]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        assert view.ladder.bucket_of(product=products[0]).key == "d30"

    def test_total_equals_sum_of_buckets(self):
        """金额守恒：所有桶加起来必须等于固收总额，否则有产品被漏掉。"""
        products = [
            mk("A", amount="1000", maturity=TODAY - timedelta(days=5)),
            mk("B", amount="2000"),
            mk("C", amount="3000", maturity=TODAY + timedelta(days=400)),
        ]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        assert view.ladder.bucket_total == view.ladder.total_amount


# --------------------------------------------------------------------------
# 发行方集中度
# --------------------------------------------------------------------------
class TestInstitutionConcentration:
    def test_concentration_by_name_keyword(self):
        products = [
            mk("招银理财招睿添利", amount="100000"),
            mk("招银理财招睿添利2", amount="100000"),
            mk("工银双玺债券", amount="100000"),
        ]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        conc = view.concentration
        assert conc.top1_name == "招行"  # 规范化后的名字
        assert conc.top1_amount == Decimal(200000)
        assert conc.top1_share == pytest.approx(2 / 3, abs=1e-6)

    def test_hhi_detects_concentration(self):
        """HHI: 全部集中在一处应远高于均匀分布。"""
        concentrated = build_fixed_income_risk_view(
            [mk("招银理财A", amount="100000"), mk("招银理财B", amount="100000")],
            as_of=TODAY,
        ).concentration
        spread = build_fixed_income_risk_view(
            [mk("招银理财A", amount="50000"), mk("工银双玺", amount="50000")],
            as_of=TODAY,
        ).concentration
        assert concentrated.hhi > spread.hhi
        assert concentrated.hhi == pytest.approx(1.0, abs=1e-6)

    def test_channel_is_not_treated_as_issuer(self):
        """代销渠道不是信用发行方，必须和发行方分开统计。

        实测支付宝渠道下同时有货币基金/债券/券商理财/高端理财——把渠道当发行方算 HHI
        会得出「支付宝占固收 15%」这种误导性结论（支付宝≈货基，信用风险接近存款）。
        """
        products = [
            mk("余额宝", itype="货币", amount="60000", platforms={"alipay": "60000"}),
            mk("工银双玺6个月", amount="40000"),
        ]
        conc = build_fixed_income_risk_view(products, as_of=TODAY).concentration
        # top1_share 对整个固收总额算（工行 40000/100000=40%）
        assert conc.top1_name == "工行"
        assert conc.top1_share == pytest.approx(0.4, abs=1e-6)
        # HHI 归一化到「已识别的发行方」口径：只有一个发行方 → 1.0。
        # 不用整个组合做分母，否则未归属部分会被当成「不集中」而低估集中度；
        # 代价是要和 issuer_attribution_rate(=0.4) 一起读才知道样本基础有多小。
        assert conc.hhi == pytest.approx(1.0, abs=1e-6)
        assert conc.issuer_attribution_rate == pytest.approx(0.4, abs=1e-6)
        # 渠道单独成列
        assert conc.channel_top1_name == "支付宝"
        assert conc.channel_top1_amount == Decimal(60000)

    def test_issuer_attribution_rate_reported(self):
        """名称命中率要单独报——实测只有 16/69 能从名称认出机构。"""
        products = [
            mk("工银双玺6个月", amount="40000"),
            mk("某未知产品", amount="60000", platforms={"alipay": "60000"}),
        ]
        conc = build_fixed_income_risk_view(products, as_of=TODAY).concentration
        assert conc.issuer_attribution_rate == pytest.approx(0.4, abs=1e-6)
        assert conc.unattributed_amount == Decimal(60000)

    def test_unattributed_amount_tracked(self):
        """名称无机构 + 无平台渠道 → 只能记为未归属，不能瞎猜一个发行方。"""
        products = [mk("完全无从判断", amount="12345")]
        conc = build_fixed_income_risk_view(products, as_of=TODAY).concentration
        assert conc.total_amount == Decimal(12345)
        assert conc.unattributed_count == 1
        assert conc.unattributed_amount == Decimal(12345)
        assert conc.top1_name is None
        assert conc.hhi == 0.0

    def test_same_bank_under_different_names_is_merged(self):
        """『招银理财』和『招商银行』是同一家——不能拆成两个桶。

        拆开会同时高估 top3 家数、低估单家集中度：实测 CSV 里两种叫法都出现过。
        """
        products = [
            mk("招银理财招睿添利90天", amount="100000"),
            mk("招商银行睿达3个月6号", amount="100000"),
            mk("工银双玺6个月", amount="100000"),
        ]
        conc = build_fixed_income_risk_view(products, as_of=TODAY).concentration
        names = [e.name for e in conc.exposures]
        assert "招银" not in names, f"「招银」没归一到「招行」: {names}"
        assert names.count("招行") == 1, f"同一家被拆成多桶: {names}"
        assert conc.top1_name == "招行"
        assert conc.top1_amount == Decimal(200000)
        assert conc.top1_share == pytest.approx(2 / 3, abs=1e-6)

    def test_icbc_short_and_full_name_merged(self):
        conc = build_fixed_income_risk_view(
            [mk("工银双玺", amount="1000"), mk("工商银行睿达", amount="1000")], as_of=TODAY
        ).concentration
        assert conc.top1_name == "工行"
        assert conc.top1_amount == Decimal(2000)

    def test_channel_labels_have_no_raw_keys(self):
        """渠道名要是人话，不能把内部键（bocom/futu）漏到 UI 上。"""
        products = [
            mk("某某A", amount="1000", platforms={"bocom": "1000"}),
            mk("某某B", amount="1000", platforms={"futu": "1000"}),
        ]
        conc = build_fixed_income_risk_view(products, as_of=TODAY).concentration
        names = [e.name for e in conc.channel_exposures]
        assert names == ["交行", "富途"], names

    def test_channel_hhi_is_separate_from_issuer_hhi(self):
        products = [
            mk("工银A", amount="10000", platforms={"cmb": "10000"}),
            mk("工银B", amount="10000", platforms={"cmb": "10000"}),
        ]
        conc = build_fixed_income_risk_view(products, as_of=TODAY).concentration
        assert conc.issuer_hhi == pytest.approx(1.0, abs=1e-6)
        assert conc.channel_hhi == pytest.approx(1.0, abs=1e-6)
        assert conc.channel_top1_name == "招行"

    def test_concentration_ignores_non_fixed_income(self):
        """股票/基金不该混进固收集中度——口径隔离。"""
        products = [mk("某理财", itype="理财", amount="10000")]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        assert view.concentration.total_amount == Decimal(10000)
        stocky = build_fixed_income_risk_view([mk("宁德时代", itype="股票", amount="10000")], as_of=TODAY)
        assert stocky.fixed_income_count == 0


# --------------------------------------------------------------------------
# 收益异常
# --------------------------------------------------------------------------
class TestYieldAnomaly:
    def test_flags_impossible_annualized_return(self):
        """纯固收产品年化 52.98% 只能是 CSV 填错（把累计收益当成了年化）。"""
        products = [mk("建信理财固收类180天", annual="52.98", compound="62.73")]
        anomalies = build_fixed_income_risk_view(products, as_of=TODAY).yield_anomalies
        kinds = {a.kind for a in anomalies}
        assert "implausible_annualized" in kinds

    def test_equity_product_with_absurd_return_not_a_fixed_income_anomaly(self):
        """实测『广发创业板ETF联接Y』年化 52.98%——它是权益，不是固收数据错误。

        归错类会让人去查固收账目，实际该看的是基金本身是不是买错了。
        """
        view = build_fixed_income_risk_view(
            [mk("广发创业板ETF联接Y", itype="个人养老金", annual="52.98", compound="62.73")],
            as_of=TODAY,
        )
        assert {a.kind for a in view.yield_anomalies} == set()
        assert view.equity_exposure_count == 1

    def test_flags_annual_vs_compound_divergence(self):
        products = [mk("南方中债7-10年国开", annual="21.22", compound="22.26")]
        anomalies = build_fixed_income_risk_view(products, as_of=TODAY).yield_anomalies
        assert any(a.kind == "compound_divergence" for a in anomalies)

    def test_normal_product_not_flagged(self):
        products = [mk("工银双玺6个月", annual="2.85", compound="2.90", days=180)]
        anomalies = build_fixed_income_risk_view(products, as_of=TODAY).yield_anomalies
        assert list(anomalies) == []

    def test_negative_return_flagged_as_loss(self):
        products = [mk("亏损债基", annual="-1.2", compound="-1.3")]
        anomalies = build_fixed_income_risk_view(products, as_of=TODAY).yield_anomalies
        assert any(a.kind == "negative_return" for a in anomalies)

    def test_annual_only_product_not_flagged_for_divergence(self):
        """只有年化没有复利年化时，不该报『两者背离』。"""
        products = [mk("只有年化", annual="2.5")]
        anomalies = build_fixed_income_risk_view(products, as_of=TODAY).yield_anomalies
        assert not any(a.kind == "compound_divergence" for a in anomalies)

    def test_anomaly_severity_ordered(self):
        products = [
            mk("荒谬", annual="52.98"),
            mk("微负", annual="-0.1"),
        ]
        anomalies = build_fixed_income_risk_view(products, as_of=TODAY).yield_anomalies
        assert anomalies[0].severity > anomalies[-1].severity


# --------------------------------------------------------------------------
# 数据完整度
# --------------------------------------------------------------------------
class TestDataQuality:
    def test_open_ended_is_not_counted_as_missing(self):
        """实测『到期时间』列从不空白：92 行是『可赎』。

        把『可赎』算成「缺到期日」会虚报 86% 的数据缺失率，误导去补数据——
        开放型产品本来就不该有到期日。开放率要单独报。
        """
        products = [mk("A", maturity=TODAY + timedelta(days=100))]
        products += [mk(f"可赎{i}") for i in range(9)]
        dq = build_fixed_income_risk_view(
            products, as_of=TODAY, raw_maturity={f"可赎{i}": "可赎" for i in range(9)}
        ).data_quality
        assert dq.missing_maturity_count == 0
        assert dq.missing_maturity_rate == 0.0
        assert dq.open_ended_count == 9
        assert dq.open_ended_rate == pytest.approx(0.9, abs=1e-6)

    def test_reports_missing_field_rates(self):
        products = [mk(f"P{i}", maturity=None, days=None) for i in range(10)]
        products[0].maturity_date = TODAY + timedelta(days=100)
        products[0].investment_days = 30
        dq = build_fixed_income_risk_view(products, as_of=TODAY).data_quality
        # 没给 raw_maturity 时，maturity_date=None 就是真缺失
        assert dq.missing_maturity_rate == pytest.approx(0.9, abs=1e-6)
        assert dq.missing_days_rate == pytest.approx(0.9, abs=1e-6)

    def test_dirty_maturity_counted_separately_from_missing(self):
        products = [mk("脏的", maturity=None), mk("好的", maturity=TODAY)]
        dq = build_fixed_income_risk_view(products, as_of=TODAY, raw_maturity={"脏的": "2938146"}).data_quality
        assert dq.dirty_maturity_count == 1
        assert dq.missing_maturity_count == 0

    def test_ladder_confidence_downgrades_when_mostly_missing(self):
        products = [mk("有到期", maturity=TODAY + timedelta(days=60))]
        products += [mk(f"缺{i}") for i in range(9)]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        assert view.ladder.confidence == "low"

    def test_ladder_confidence_high_when_mostly_dated(self):
        products = [mk(f"P{i}", maturity=TODAY + timedelta(days=60 + i)) for i in range(10)]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        assert view.ladder.confidence == "high"


# --------------------------------------------------------------------------
# 顶层组装
# --------------------------------------------------------------------------
class TestBuildView:
    def test_only_fixed_income_included(self):
        products = [
            mk("理财A", itype="理财", amount="10000"),
            mk("债券A", itype="债券", amount="20000"),
            mk("货币A", itype="货币", amount="30000"),
            mk("股票A", itype="股票", amount="999999"),
            mk("基金A", itype="基金", amount="888888"),
        ]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        assert view.fixed_income_count == 3
        assert view.total_amount == Decimal(60000)
        assert view.equity_or_fund_excluded_amount == Decimal(1888887)

    def test_as_of_recorded_in_output(self):
        """as-of 必须显式落进结果——合并两个数据源时不能靠猜。"""
        view = build_fixed_income_risk_view([mk("A")], as_of=TODAY)
        assert view.as_of == TODAY
        assert view.to_dict()["as_of"] == "2026-10-01"

    def test_empty_input_is_safe(self):
        view = build_fixed_income_risk_view([], as_of=TODAY)
        assert view.fixed_income_count == 0
        assert view.total_amount == Decimal(0)
        assert view.to_dict()["as_of"] == "2026-10-01"

    def test_headline_alerts_rank_overdue_first(self):
        products = [
            mk("逾期", amount="100000", maturity=TODAY - timedelta(days=90)),
            mk("脏数据", amount="50000"),
        ]
        view = build_fixed_income_risk_view(products, as_of=TODAY, raw_maturity={"脏数据": "2938146"})
        assert view.alerts
        assert view.alerts[0].kind == "overdue"

    def test_to_dict_is_json_serializable(self):
        import json

        view = build_fixed_income_risk_view([mk("A", maturity=TODAY + timedelta(days=10), annual="2.5")], as_of=TODAY)
        json.dumps(view.to_dict())  # 不抛异常即可

    def test_foreign_currency_converted(self):
        """美元固收要按汇率折算，否则集中度/梯队金额全错。

        币种不是字段，是 investment_type 隐含的（InvestmentProduct 没有 currency）。
        口径必须和 data/portfolio.py 的 total_value 一致，否则两个视图的总额对不上。
        """
        p = mk("高腾微金美元货币基金", amount="1000", itype="美元基金（美元）")
        view = build_fixed_income_risk_view([p], as_of=TODAY, usd_rate=Decimal("7"))
        assert view.fixed_income_count == 1
        assert view.total_amount == Decimal(7000)

    def test_usd_rate_on_product_takes_precedence(self):
        p = mk("高腾微金美元货币基金", amount="1000", itype="美元基金（美元）")
        p.usd_rate = Decimal("6.7945")  # CSV 自带汇率
        view = build_fixed_income_risk_view([p], as_of=TODAY, usd_rate=Decimal("7"))
        assert view.total_amount == Decimal(1000) * Decimal("6.7945")


class TestEquityExposureSplit:
    """固收+（含权益敞口）必须和纯固收分开。

    实测踩到的坑：CSV 类型是『个人养老金』/『理财』的产品里装着 ETF联接、指数增强、
    混合类——把它们的负收益报成『固收+ 收益异常』是范畴错误。沪深300 指数增强跌 17%
    是权益波动，不是信用事件。该看的还是要看，但要用对的口径。
    """

    def test_equity_exposed_products_split_out(self):
        products = [
            mk("国泰海通沪深300指数增强A", itype="个人养老金", amount="100000", annual="-17.0"),
            mk("鹏华弘康灵活配置混合C", itype="理财", amount="50000", annual="-3.0"),
            mk("华安安浦债券A", itype="债券", amount="50000", annual="2.5"),
        ]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        # 纯固收只剩华安安浦债券
        assert view.fixed_income_count == 1
        assert view.total_amount == Decimal(50000)
        # 含权益敞口的单独统计
        assert view.equity_exposure_count == 2
        assert view.equity_exposure_amount == Decimal(150000)
        assert view.equity_exposure_losing_count == 2

    def test_equity_loss_is_not_a_fixed_income_anomaly(self):
        """权益产品的负收益不该进固收收益异常表——会误导成信用问题。"""
        products = [mk("国泰海通沪深300指数增强A", itype="个人养老金", amount="100000", annual="-17.0")]
        kinds = {a.kind for a in build_fixed_income_risk_view(products, as_of=TODAY).yield_anomalies}
        assert "negative_return" not in kinds

    def test_equity_exposure_reported_as_its_own_alert(self):
        """但仍要提示——权益仓位跌 17% 是用户该知道的事，只是口径要对。"""
        products = [
            mk("国泰海通沪深300指数增强A", itype="个人养老金", amount="100000", annual="-17.0"),
        ]
        alerts = build_fixed_income_risk_view(products, as_of=TODAY).alerts
        assert any(a.kind == "equity_exposure_loss" for a in alerts)

    def test_equity_keywords_cover_pension_etf_link(self):
        products = [
            mk("广发创业板ETF联接Y", itype="个人养老金", amount="1000", annual="-1.4"),
            mk("易方达中证红利ETF联接发起式Y", itype="个人养老金", amount="1000", annual="-0.5"),
        ]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        assert view.equity_exposure_count == 2
        assert view.fixed_income_count == 0

    def test_bond_plus_product_not_counted_as_equity(self):
        """『固收增强』是固收+（少量权益），不是纯固收，但也不能算成权益基金。"""
        products = [mk("慧盈象固收增利6M持有期15号A", itype="理财", amount="1000", annual="2.0")]
        view = build_fixed_income_risk_view(products, as_of=TODAY)
        # 增利/持有期 不在权益关键词里 → 留在固收+
        assert view.fixed_income_count == 1


def test_fixed_income_types_excludes_equity():
    from asset_lens.data.models import InvestmentType

    assert InvestmentType.STOCK not in FIXED_INCOME_TYPES
    assert InvestmentType.US_STOCK not in FIXED_INCOME_TYPES
    assert InvestmentType.ETF not in FIXED_INCOME_TYPES
    assert InvestmentType.GOLD not in FIXED_INCOME_TYPES
    assert InvestmentType.WEALTH in FIXED_INCOME_TYPES
    assert InvestmentType.BOND in FIXED_INCOME_TYPES
