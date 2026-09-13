
        const { createApp, ref, onMounted, nextTick, computed, watch } = Vue;

        createApp({
            setup() {
                const currentTab = ref('overview');
                const loading = ref(true);
                const refreshing = ref(false);
                const tabLoading = ref(false);
                const error = ref('');
                const mobileMenuOpen = ref(false);
                const isDemoMode = ref(false);
                const demoBannerClosed = ref(false);
                const summary = ref({
                    total_assets: 0,
                    total_assets_overview: 0,
                    total_profit: 0,
                    total_return: 0,
                    position_count: 0
                });
                const portfolioItems = ref([]);
                const riskScore = ref(50);
                const riskLevel = ref('中等');
                const riskData = ref({ dimensions: null, warnings: [], suggestions: [] });
                const wealthData = ref({ total_amount: 0, ratio: 0, product_count: 0, avg_annual_return: 0, negative_count: 0, negative_products: [], institutions: [], risk_distribution: {}, term_distribution: {}, products: [] });
                const equityData = ref({ total_amount: 0, ratio: 0, product_count: 0, avg_return: 0, positive_count: 0, negative_count: 0, negative_products: [], categories: [], risk_distribution: {}, held_distribution: {}, advice: [], products: [] });
                const fiData = ref({ total_amount: 0, ratio: 0, product_count: 0, avg_return: 0, avg_annualized: 0, negative_count: 0, negative_products: [], categories: [], risk_distribution: {}, held_distribution: {}, portfolio_insights: [], advice: [], products: [] });
                const remData = ref({ total_amount: 0, ratio: 0, product_count: 0, avg_return: null, avg_annualized: null, negative_count: 0, negative_products: [], categories: [], risk_distribution: {}, held_distribution: {}, portfolio_insights: [], advice: [], products: [] });
                const trendData = ref({ dates: [], total: [], accounts: {}, benchmarks: {}, summary: null });
                const marketAdvice = ref({ data_date: '', categories: [], indicators: [], note: '', source_file: '', updated_at: '', mode: '', portfolio_source: {} });
                const moneyRatio = computed(() => {
                    const cat = (remData.value.categories || []).find(c => c.name === '货币/现金');
                    return cat ? cat.ratio : 0;
                });
                const visibleEquityAdvice = computed(() => (equityData.value.advice || []).filter(a => a.priority !== 'low'));
                const configCategories = computed(() => {
                    const total = summary.value.total_assets || 1;
                    const rem = remData.value.products || [];
                    const sumCat = (k) => rem.filter(p => (p.category || '').includes(k)).reduce((a, p) => a + (p.amount_cny || 0), 0);
                    const advice = (marketAdvice.value.categories || []);
                    const range = (name, defMin, defMax) => {
                        const a = advice.find(c => c.name === name);
                        return a && typeof a.min === 'number' && typeof a.max === 'number' ? { min: a.min, max: a.max } : { min: defMin, max: defMax };
                    };
                    const r1 = range('理财类', 15, 35);
                    const r2 = range('固收类', 30, 50);
                    const r3 = range('权益类', 10, 30);
                    const r4 = range('现金储备', 5, 15);
                    const r5 = range('黄金', 0, 10);
                    const r6 = range('养老储备', 0, 10);
                    const cats = [
                        { name: '理财类', value: wealthData.value.total_amount || 0, min: r1.min, max: r1.max },
                        { name: '固收类', value: fiData.value.total_amount || 0, min: r2.min, max: r2.max },
                        { name: '权益类', value: equityData.value.total_amount || 0, min: r3.min, max: r3.max },
                        { name: '现金储备', value: sumCat('货币'), min: r4.min, max: r4.max },
                        { name: '黄金', value: sumCat('黄金'), min: r5.min, max: r5.max },
                        { name: '养老储备', value: sumCat('养老'), min: r6.min, max: r6.max }
                    ];
                    return cats.map(c => {
                        const pct = (c.value / total) * 100;
                        return { ...c, pct, status: pct < c.min ? 'low' : (pct > c.max ? 'high' : 'ok') };
                    });
                });
                const maturityReminders = computed(() => {
                    const cutoff = 90;
                    return (wealthData.value.products || [])
                        .filter(p => p.days_to_maturity !== null && p.days_to_maturity !== undefined && p.days_to_maturity <= cutoff)
                        .sort((a, b) => a.days_to_maturity - b.days_to_maturity);
                });
                const lastUpdate = ref('');
                const allocationLoading = ref(false);
                let _allocLoadGen = 0;
                
                const currentPage = ref(1);
                const pageSize = ref(15);

                const totalPages = computed(() => Math.ceil(portfolioItems.value.length / pageSize.value));
                const highRiskProducts = computed(() => (wealthData.value.products || []).filter(p => p.risk_score >= 65));

                const detailData = ref(null);
                const openDetail = (p) => { detailData.value = p; };
                const closeDetail = () => { detailData.value = null; };

                const equityDetail = ref(null);
                const openEquityDetail = (p) => { equityDetail.value = p; };
                const closeEquityDetail = () => { equityDetail.value = null; };
                const fiDetail = ref(null);
                const openFiDetail = (p) => { fiDetail.value = p; };
                const closeFiDetail = () => { fiDetail.value = null; };
                const fiGroupDetail = ref(null);
                const openFiGroupDetail = (title, products) => {
                    const list = (products || []).map(p => ({ name: p.name, amount_cny: p.amount_cny, annual_return: p.annual_return, annualized_return: p.annualized_return }));
                    list.sort((a, b) => b.amount_cny - a.amount_cny);
                    fiGroupDetail.value = {
                        title,
                        products: list,
                        total: list.reduce((s, p) => s + (p.amount_cny || 0), 0)
                    };
                };
                const closeFiGroupDetail = () => { fiGroupDetail.value = null; };
                const portfolioDetail = ref(null);
                const openPortfolioDetail = (item) => {
                    portfolioDetail.value = {
                        name: item.name,
                        code: item.code || '',
                        type: item.investment_type || item.type || '其他',
                        currency: item.currency || 'CNY',
                        original_amount: item.original_amount != null ? item.original_amount : null,
                        current_amount: item.current_amount != null ? item.current_amount : 0,
                        initial_amount: item.initial_amount != null ? item.initial_amount : 0,
                        profit_amount: item.profit_amount || item.profit || 0,
                        return_rate: item.return_rate || item.profit_rate || 0,
                        annual_return: item.annual_return != null ? item.annual_return : null,
                        risk_level: item.risk_level || '未知'
                    };
                };
                const closePortfolioDetail = () => { portfolioDetail.value = null; };
                const chartCtx = () => ({
                    portfolioItems: portfolioItems.value,
                    riskData: riskData.value,
                    wealthData: wealthData.value,
                    equityData: equityData.value,
                    fiData: fiData.value,
                    remData: remData.value,
                    trendData: trendData.value,
                    summary: summary.value,
                    marketAdvice: marketAdvice.value,
                    openFiGroupDetail,
                });
                const remDetail = ref(null);
                const openRemDetail = (p) => { remDetail.value = p; };
                const closeRemDetail = () => { remDetail.value = null; };
                const paginatedItems = computed(() => {
                    const start = (currentPage.value - 1) * pageSize.value;
                    const end = start + pageSize.value;
                    return portfolioItems.value.slice(start, end);
                });

                let charts = {
                    allocation: null,
                    profit: null,
                    risk: null,
                    strategy: null,
                    strategyRisk: null,
                    wealthInst: null,
                    wealthRisk: null,
                    wealthTerm: null,
                    wealthHeld: null,
                    equityCat: null,
                    equityRisk: null,
                    equityRet: null,
                    equityHeld: null
                };

                const API_BASE = window.location.origin;

                const toggleMobileMenu = () => {
                    mobileMenuOpen.value = !mobileMenuOpen.value;
                };

                const closeMobileMenu = () => {
                    mobileMenuOpen.value = false;
                };

                const prevPage = () => {
                    if (currentPage.value > 1) {
                        currentPage.value--;
                    }
                };

                const nextPage = () => {
                    if (currentPage.value < totalPages.value) {
                        currentPage.value++;
                    }
                };

                const fetchData = async (isInitial = false) => {
                    if (isInitial) {
                        loading.value = true;
                    } else {
                        tabLoading.value = true;
                    }
                    allocationLoading.value = true;
                    const _allocGen = ++_allocLoadGen;
                    const _allocStartedAt = Date.now();
                    error.value = '';
                    try {
                        // 检测 Demo 模式
                        const demoRes = await fetch(`${API_BASE}/api/demo/status`).then(r => r.json()).catch(() => ({ demo_mode: false }));
                        isDemoMode.value = demoRes.demo_mode || false;

                        const [summaryRes, portfolioRes, riskRes] = await Promise.all([
                            fetch(`${API_BASE}/api/portfolio/summary`).then(r => r.json()),
                            fetch(`${API_BASE}/api/portfolio/items`).then(r => r.json()).catch(() => ({ items: [] })),
                            fetch(`${API_BASE}/api/risk/summary`).then(r => r.json()).catch(() => ({}))
                        ]);
                        const wealthRes = await fetch(`${API_BASE}/api/wealth/overview`).then(r => r.json()).catch(() => ({}));
                        const equityRes = await fetch(`${API_BASE}/api/equity/overview`).then(r => r.json()).catch(() => ({}));
                        const fiRes = await fetch(`${API_BASE}/api/fixed-income/overview`).then(r => r.json()).catch(() => ({}));
                        const remRes = await fetch(`${API_BASE}/api/remaining/overview`).then(r => r.json()).catch(() => ({}));
                        const trendRes = await fetch(`${API_BASE}/api/trend/overview`).then(r => r.json()).catch(() => ({}));
                        const marketAdviceRes = await fetch(`${API_BASE}/api/market/advice`).then(r => r.json()).catch(() => ({}));

                        summary.value = summaryRes;
                        marketAdvice.value = marketAdviceRes;
                        portfolioItems.value = portfolioRes.items || [];
                        if (riskRes && typeof riskRes.risk_score === 'number') {
                            riskScore.value = riskRes.risk_score;
                            riskLevel.value = riskRes.risk_level || riskLevel.value;
                            riskData.value = {
                                dimensions: riskRes.dimensions || null,
                                warnings: riskRes.warnings || [],
                                suggestions: riskRes.suggestions || []
                            };
                        }
                        if (wealthRes && wealthRes.product_count > 0) {
                            wealthData.value = wealthRes;
                        }
                        if (equityRes && equityRes.product_count > 0) {
                            equityData.value = equityRes;
                        }
                        if (fiRes && fiRes.product_count > 0) {
                            fiData.value = fiRes;
                        }
                        if (remRes && remRes.product_count > 0) {
                            remData.value = remRes;
                        }
                        if (trendRes && trendRes.summary) {
                            trendData.value = trendRes;
                        }
                        lastUpdate.value = new Date().toLocaleString('zh-CN');
                    } catch (e) {
                        error.value = '加载数据失败: ' + e.message;
                    } finally {
                        // 先放行内容区渲染（v-if="!loading"），图表容器才会出现在 DOM
                        if (isInitial) {
                            loading.value = false;
                        } else {
                            tabLoading.value = false;
                        }
                    }
                    // 内容区已渲染，再初始化图表（等容器就绪逻辑在 initAllocationChart 内）
                    await nextTick();
                    await AssetCharts.initAllocationChart(charts, chartCtx());
                    // 图表完成后再关闭模块 loading（最小展示 400ms）
                    const remain = Math.max(0, 400 - (Date.now() - _allocStartedAt));
                    setTimeout(() => {
                        if (_allocGen === _allocLoadGen) allocationLoading.value = false;
                    }, remain);
                };






                const switchTab = async (tab) => {
                    currentTab.value = tab;
                    closeMobileMenu();
                    await nextTick();
                    
                    if (tab === 'overview') {
                        AssetCharts.initAllocationChart(charts, chartCtx());
                    } else if (tab === 'trend') {
                        AssetCharts.initTrendCharts(charts, chartCtx());
                    } else if (tab === 'portfolio') {
                        AssetCharts.initProfitChart(charts, chartCtx());
                    } else if (tab === 'portfolio_config') {
                        AssetCharts.initPortfolioConfigChart(charts, chartCtx());
                    } else if (tab === 'risk') {
                        AssetCharts.initRiskChart(charts, chartCtx());
                    } else if (tab === 'wealth') {
                        AssetCharts.initWealthCharts(charts, chartCtx());
                    } else if (tab === 'fixed_income') {
                        AssetCharts.initFixedIncomeCharts(charts, chartCtx());
                    } else if (tab === 'equity') {
                        AssetCharts.initEquityCharts(charts, chartCtx());
                    } else if (tab === 'remaining') {
                        AssetCharts.initRemainingCharts(charts, chartCtx());
                    }
                };

                const refreshPortfolio = async () => {
                    refreshing.value = true;
                    try {
                        await fetchData();
                    } finally {
                        refreshing.value = false;
                    }
                };

                const formatMoney = (value) => {
                    if (value === null || value === undefined) return '¥0';
                    const num = parseFloat(value);
                    if (isNaN(num)) return '¥0';
                    if (num >= 10000) {
                        return '¥' + (num / 10000).toFixed(2) + '万';
                    }
                    return '¥' + num.toFixed(2);
                };

                // 按币种显示金额：USD/HKD 显示原币，CNY 用 ¥
                const formatMoneyByCurrency = (p) => {
                    if (!p) return formatMoney(0);
                    const num = parseFloat(p.amount) || 0;
                    if (p.currency === 'USD') return '$' + num.toFixed(2);
                    if (p.currency === 'HKD') return 'HK$' + num.toFixed(2);
                    return formatMoney(num);
                };

                // 万元带符号两位小数（与 CLI 打印口径一致）：12345 -> +1.23万
                const formatWanSigned = (value) => {
                    if (value === null || value === undefined || isNaN(parseFloat(value))) return '0万';
                    const wan = parseFloat(value) / 10000;
                    const sign = wan > 0 ? '+' : (wan < 0 ? '-' : '');
                    return sign + Math.abs(wan).toFixed(2) + '万';
                };

                const riskBadgeClass = (score) => {
                    if (score >= 65) return 'risk-badge-high';
                    if (score >= 45) return 'risk-badge-mid';
                    return 'risk-badge-low';
                };

                const adviceBadgeText = (priority) => {
                    if (priority === 'high') return '高优先';
                    if (priority === 'medium') return '建议';
                    return '观察';
                };

                const getTypeClass = (type) => {
                    if (!type) return 'tag';
                    const typeMap = {
                        'A股': 'tag-stock',
                        '股票': 'tag-stock',
                        '美股': 'tag-stock',
                        'ETF': 'tag-stock',
                        '基金': 'tag-fund',
                        '定投基金': 'tag-fund',
                        '个人养老金': 'tag-fund',
                        '债券': 'tag-bond',
                        '现金': 'tag-cash',
                        '货币': 'tag-cash',
                        '理财': 'tag-fund',
                        '特别国债': 'tag-bond',
                        '黄金': 'tag-stock',
                    };
                    if (type.includes('基金') || type.includes('理财')) return 'tag-fund';
                    if (type.includes('债')) return 'tag-bond';
                    if (type.includes('现金') || type.includes('货币')) return 'tag-cash';
                    return typeMap[type] || 'tag';
                };







                onMounted(() => {
                    fetchData(true);
                    window.addEventListener('resize', () => AssetCharts.handleResize(charts));
                });

                watch(currentPage, () => {
                    nextTick(() => {
                        AssetCharts.initProfitChart(charts, chartCtx());
                    });
                });

                return {
                    currentTab,
                    loading,
                    refreshing,
                    tabLoading,
                    error,
                    mobileMenuOpen,
                    isDemoMode,
                    demoBannerClosed,
                    summary,
                    portfolioItems,
                    paginatedItems,
                    currentPage,
                    totalPages,
                    pageSize,
                    riskScore,
                    riskLevel,
                    wealthData,
                    equityData,
                    fiData,
                    remData,
                    trendData,
                    moneyRatio,
                    visibleEquityAdvice,
                    configCategories,
                    maturityReminders,
                    marketAdvice,
                    highRiskProducts,
                    detailData,
                    openDetail,
                    closeDetail,
                    portfolioDetail,
                    openPortfolioDetail,
                    closePortfolioDetail,
                    equityDetail,
                    openEquityDetail,
                    closeEquityDetail,
                    openFiDetail,
                    closeFiDetail,
                    fiDetail,
                    fiGroupDetail,
                    openFiGroupDetail,
                    closeFiGroupDetail,
                    remDetail,
                    openRemDetail,
                    closeRemDetail,
                    riskBadgeClass,
                    adviceBadgeText,
                    lastUpdate,
                    refreshPortfolio,
                    switchTab,
                    formatMoney,
                    formatMoneyByCurrency,
                    formatWanSigned,
                    getTypeClass,
                    toggleMobileMenu,
                    closeMobileMenu,
                    prevPage,
                    nextPage
                };
            }
        }).mount('#app');
    