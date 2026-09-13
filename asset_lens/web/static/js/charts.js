/**
 * Asset Lens 图表模块（charts.js）
 * 与 Vue 应用解耦：所有图表初始化函数签名统一为 (charts, ctx)
 *   - charts: ECharts 实例注册表 { key: echartsInstance }
 *   - ctx: 数据上下文 { portfolioItems, riskData, wealthData, equityData, fiData, remData, trendData, openFiGroupDetail }
 */
(function () {
    const echarts = window.echarts;
    const DEBOUNCE_DELAY = 150;

    function debounce(fn, delay) {
        let timer = null;
        return function (...args) {
            if (timer) clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    function handleResize(charts) {
        Object.values(charts).forEach(chart => {
            if (chart) chart.resize();
        });
    }

                async function initAllocationChart(charts, ctx) {
                let el = document.getElementById('allocationChart');
                
                // 等待容器就绪（元素出现且有宽度）：挂载时序下容器可能尚未渲染/布局
                const deadline = Date.now() + 8000;
                while ((!el || el.clientWidth === 0) && Date.now() < deadline) {
                    el = document.getElementById('allocationChart');
                    await new Promise(r => setTimeout(r, 100));
                }
                if (!el) return;
                
                if (charts.allocation) {
                    charts.allocation.dispose();
                    charts.allocation = null;
                }

                const typeData = {};
                ctx.portfolioItems.forEach(item => {
                    const type = item.investment_type || item.type || '其他';
                    typeData[type] = (typeData[type] || 0) + parseFloat(item.current_amount || 0);
                });

                const chartData = Object.entries(typeData).map(([name, value]) => ({ name, value }));
                const isMobile = window.innerWidth <= 768;

                charts.allocation = echarts.init(el);
                
                charts.allocation.setOption({
                    tooltip: { 
                        trigger: 'item', 
                        formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)`,
                        confine: true
                    },
                    legend: { 
                        orient: isMobile ? 'horizontal' : 'vertical', 
                        left: isMobile ? 'center' : 'left', 
                        top: isMobile ? 'bottom' : 'middle',
                        textStyle: { color: '#fff', fontSize: isMobile ? 12 : 14 } 
                    },
                    series: [{
                        type: 'pie',
                        radius: isMobile ? ['30%', '50%'] : ['40%', '70%'],
                        center: isMobile ? ['50%', '40%'] : ['60%', '50%'],
                        avoidLabelOverlap: true,
                        itemStyle: { borderRadius: 10, borderColor: '#1a1a2e', borderWidth: 2 },
                        label: { show: false },
                        emphasis: { 
                            label: { show: true, fontSize: 14, fontWeight: 'bold' },
                            itemStyle: {
                                shadowBlur: 10,
                                shadowOffsetX: 0,
                                shadowColor: 'rgba(0, 0, 0, 0.5)'
                            }
                        },
                        labelLine: { show: false },
                        data: chartData,
                        animation: false
                    }]
                }, true);

                // 布局完成后再校正一次尺寸，避免容器宽 0 时画布异常
                setTimeout(() => {
                    if (charts.allocation && el.clientWidth > 0) charts.allocation.resize();
                }, 100);
                }


                async function initProfitChart(charts, ctx) {
                const el = document.getElementById('profitChart');
                if (!el) return;
                
                if (charts.profit) {
                    charts.profit.dispose();
                    charts.profit = null;
                }

                const allProfitData = ctx.portfolioItems.map(item => ({
                    name: item.name,
                    value: parseFloat(item.profit_amount || item.profit || 0)
                }));
                
                // 按收益降序（大赚 → 大亏），展示全部产品，避免抽样丢失
                allProfitData.sort((a, b) => b.value - a.value);
                const profitData = allProfitData;
                const isMobile = window.innerWidth <= 768;

                charts.profit = echarts.init(el);
                
                charts.profit.setOption({
                    tooltip: { 
                        trigger: 'axis', 
                        axisPointer: { type: 'shadow' },
                        confine: true
                    },
                    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
                    xAxis: { 
                        type: 'category', 
                        data: profitData.map(d => d.name), 
                        axisLabel: { 
                            color: '#888', 
                            rotate: isMobile ? 45 : 30,
                            fontSize: isMobile ? 10 : 12,
                            interval: 'auto'
                        } 
                    },
                    yAxis: { type: 'value', axisLabel: { color: '#888' } },
                    series: [{
                        type: 'bar',
                        barWidth: isMobile ? '60%' : 'auto',
                        large: true,
                        largeThreshold: 500,
                        data: profitData.map(d => ({
                            value: d.value,
                            itemStyle: { color: d.value >= 0 ? '#ff5252' : '#00c853' }
                        })),
                        animation: false
                    }]
                }, true);
                }


                async function initRiskChart(charts, ctx) {
                const el = document.getElementById('riskChart');
                if (!el) return;
                
                if (charts.risk) {
                    charts.risk.dispose();
                    charts.risk = null;
                }

                const isMobile = window.innerWidth <= 768;

                const dims = ctx.riskData.dimensions || { market: 0, concentration: 0, liquidity: 0, credit: 0, operational: 0 };

                charts.risk = echarts.init(el);
                
                charts.risk.setOption({
                    tooltip: { confine: true },
                    radar: {
                        indicator: [
                            { name: '市场风险', max: 100 },
                            { name: '集中度风险', max: 100 },
                            { name: '流动性风险', max: 100 },
                            { name: '信用风险', max: 100 },
                            { name: '操作风险', max: 100 }
                        ],
                        axisName: { color: '#888', fontSize: isMobile ? 10 : 12 },
                        radius: isMobile ? '60%' : '70%'
                    },
                    series: [{
                        type: 'radar',
                        data: [{
                            value: [dims.market, dims.concentration, dims.liquidity, dims.credit, dims.operational],
                            name: '风险指标',
                            areaStyle: { color: 'rgba(0, 210, 255, 0.3)' },
                            lineStyle: { color: '#00d2ff' }
                        }]
                    }]
                }, true);
                }


                async function initWealthCharts(charts, ctx) {
                const initOne = async (id, key, makeOption) => {
                    let el = document.getElementById(id);
                    const deadline = Date.now() + 8000;
                    while (!el && Date.now() < deadline) {
                        el = document.getElementById(id);
                        await new Promise(r => setTimeout(r, 100));
                    }
                    if (!el) return;
                    if (charts[key]) { charts[key].dispose(); charts[key] = null; }
                    charts[key] = echarts.init(el);
                    charts[key].setOption(makeOption(), true);
                };

                const inst = ctx.wealthData.institutions || [];
                const riskDist = ctx.wealthData.risk_distribution || {};
                const termDist = ctx.wealthData.term_distribution || {};

                await initOne('wealthInstChart', 'wealthInst', () => ({
                    tooltip: { confine: true, trigger: 'axis' },
                    grid: { left: 80, right: 30, top: 20, bottom: 50 },
                    xAxis: {
                        type: 'value',
                        axisLabel: { color: '#888', formatter: (v) => (v >= 10000 ? (v / 10000).toFixed(1) + '万' : Number(v.toFixed(0))) },
                        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } }
                    },
                    yAxis: {
                        type: 'category',
                        data: inst.map(i => i.name),
                        axisLabel: { color: '#aaa', fontSize: 11 },
                        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } }
                    },
                    series: [{
                        type: 'bar',
                        data: inst.map(i => i.amount),
                        itemStyle: { color: '#00d2ff', borderRadius: [0, 4, 4, 0] },
                        label: { show: true, position: 'right', color: '#aaa', formatter: (p) => Number(inst[p.dataIndex].ratio).toFixed(2) + '%' }
                    }]
                }));

                await initOne('wealthRiskChart', 'wealthRisk', () => {
                    const names = Object.keys(riskDist);
                    return {
                        tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                        legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                        series: [{
                            type: 'pie',
                            radius: ['45%', '70%'],
                            center: ['50%', '45%'],
                            data: names.map(n => ({ name: n, value: riskDist[n] })),
                            label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                        }]
                    };
                });

                await initOne('wealthTermChart', 'wealthTerm', () => {
                    const names = Object.keys(termDist);
                    return {
                        tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                        legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                        series: [{
                            type: 'pie',
                            radius: ['45%', '70%'],
                            center: ['50%', '45%'],
                            data: names.map(n => ({ name: n, value: termDist[n] })),
                            label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                        }]
                    };
                });

                const heldDist = ctx.wealthData.held_distribution || {};
                await initOne('wealthHeldChart', 'wealthHeld', () => {
                    const names = Object.keys(heldDist);
                    const order = ['新买入', '短期', '中期', '长期'];
                    names.sort((a, b) => order.indexOf(a) - order.indexOf(b));
                    return {
                        tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                        legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                        series: [{
                            type: 'pie',
                            radius: ['45%', '70%'],
                            center: ['50%', '45%'],
                            data: names.map(n => ({ name: n, value: heldDist[n] })),
                            label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                        }]
                    };
                });
                }


                async function initEquityCharts(charts, ctx) {
                const initOne = async (id, key, makeOption) => {
                    let el = document.getElementById(id);
                    const deadline = Date.now() + 8000;
                    while (!el && Date.now() < deadline) {
                        el = document.getElementById(id);
                        await new Promise(r => setTimeout(r, 100));
                    }
                    if (!el) return;
                    if (charts[key]) { charts[key].dispose(); charts[key] = null; }
                    charts[key] = echarts.init(el);
                    charts[key].setOption(makeOption(), true);
                };

                const catDist = (ctx.equityData.categories || []).map(c => ({ name: c.name, value: c.amount }));
                const riskDist = ctx.equityData.risk_distribution || {};
                const heldDist = ctx.equityData.held_distribution || {};
                const products = ctx.equityData.products || [];

                await initOne('equityCatChart', 'equityCat', () => ({
                    tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                    legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                    series: [{
                        type: 'pie',
                        radius: ['45%', '70%'],
                        center: ['50%', '45%'],
                        data: catDist,
                        label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                    }]
                }));

                await initOne('equityRiskChart', 'equityRisk', () => {
                    const names = Object.keys(riskDist);
                    return {
                        tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                        legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                        series: [{
                            type: 'pie',
                            radius: ['45%', '70%'],
                            center: ['50%', '45%'],
                            data: names.map(n => ({ name: n, value: riskDist[n] })),
                            label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                        }]
                    };
                });

                await initOne('equityRetChart', 'equityRet', () => {
                    // 收益区间分布：避免 30 个产品名堆叠，按收益率分档统计
                    const ranges = [
                        { label: '亏损>10%', min: -Infinity, max: -10 },
                        { label: '亏损0~10%', min: -10, max: 0 },
                        { label: '盈利0~5%', min: 0, max: 5 },
                        { label: '盈利5~15%', min: 5, max: 15 },
                        { label: '盈利15~25%', min: 15, max: 25 },
                        { label: '盈利>25%', min: 25, max: Infinity }
                    ];
                    const dist = ranges.map(r => {
                        const list = products.filter(p => p.annual_return >= r.min && p.annual_return < r.max);
                        return {
                            name: r.label,
                            count: list.length,
                            amount: list.reduce((s, p) => s + (p.amount || 0), 0),
                            list
                        };
                    });
                    const bucketTip = (d) => {
                        const items = d.list.slice().sort((a, b) => (b.amount || 0) - (a.amount || 0)).slice(0, 8)
                            .map(p => `· ${(p.name || '').slice(0, 14)} ¥${((p.amount || 0) / 10000).toFixed(1)}万`).join('<br>');
                        const more = d.list.length > 8 ? `<br>… 等 ${d.list.length} 个产品` : '';
                        return `${d.name}<br>产品数：${d.count} 个 · 金额：¥${(d.amount / 10000).toFixed(1)}万${items ? '<br>' + items : ''}${more}`;
                    };
                    return {
                        tooltip: {
                            confine: true,
                            trigger: 'axis',
                            axisPointer: { type: 'shadow' },
                            formatter: (params) => {
                                const d = dist[params[0].dataIndex];
                                return bucketTip(d);
                            }
                        },
                        grid: { left: 50, right: 20, top: 30, bottom: 30 },
                        xAxis: {
                            type: 'category',
                            data: dist.map(d => d.name),
                            axisLabel: { color: '#8899aa', fontSize: 11, interval: 0 }
                        },
                        yAxis: { type: 'value', name: '产品数', minInterval: 1, axisLabel: { color: '#8899aa' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } } },
                        series: [{
                            type: 'bar',
                            data: dist.map((d, i) => ({
                                value: d.count,
                                itemStyle: {
                                    color: ['#008a4a', '#66bb6a', '#aed581', '#ffb07a', '#ff5252', '#d32f2f'][i],
                                    borderRadius: [4, 4, 0, 0]
                                }
                            })),
                            label: { show: true, position: 'top', color: '#aaa', fontSize: 11, formatter: '{c}个' },
                            barWidth: '55%'
                        }]
                    };
                });

                await initOne('equityHeldChart', 'equityHeld', () => {
                    const names = Object.keys(heldDist);
                    const order = ['新买入', '短期', '中期', '长期'];
                    names.sort((a, b) => order.indexOf(a) - order.indexOf(b));
                    return {
                        tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                        legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                        series: [{
                            type: 'pie',
                            radius: ['45%', '70%'],
                            center: ['50%', '45%'],
                            data: names.map(n => ({ name: n, value: heldDist[n] })),
                            label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                        }]
                    };
                });
                }


                async function initFixedIncomeCharts(charts, ctx) {
                const initOne = async (id, key, makeOption) => {
                    let el = document.getElementById(id);
                    const deadline = Date.now() + 8000;
                    while (!el && Date.now() < deadline) {
                        el = document.getElementById(id);
                        await new Promise(r => setTimeout(r, 100));
                    }
                    if (!el) return null;
                    if (charts[key]) { charts[key].dispose(); charts[key] = null; }
                    charts[key] = echarts.init(el);
                    charts[key].setOption(makeOption(), true);
                    return charts[key];
                };

                const catDist = (ctx.fiData.categories || []).map(c => ({ name: c.name, value: c.amount }));
                const riskDist = ctx.fiData.risk_distribution || {};
                const heldDist = ctx.fiData.held_distribution || {};
                const products = ctx.fiData.products || [];
                const isMobile = window.innerWidth <= 768;
                const openGroup = (name, filter) => {
                    const list = products.filter(filter);
                    if (!list.length) return;
                    ctx.openFiGroupDetail(`${name}（${list.length} 个）`, list);
                };

                const catChart = await initOne('fiCatChart', 'fiCat', () => ({
                    tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                    legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                    series: [{
                        type: 'pie',
                        radius: ['45%', '70%'],
                        center: ['50%', '45%'],
                        data: catDist,
                        label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                    }]
                }));
                if (catChart) catChart.on('click', (p) => openGroup(p.name, (x) => x.category === p.name));

                const riskChart = await initOne('fiRiskChart', 'fiRisk', () => {
                    const names = Object.keys(riskDist);
                    const order = ['低', '中低', '中', '中高', '高'];
                    names.sort((a, b) => order.indexOf(a) - order.indexOf(b));
                    return {
                        tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                        legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                        series: [{
                            type: 'pie',
                            radius: ['45%', '70%'],
                            center: ['50%', '45%'],
                            data: names.map(n => ({ name: n, value: riskDist[n] })),
                            label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                        }]
                    };
                });
                if (riskChart) riskChart.on('click', (p) => openGroup(p.name, (x) => x.risk_level === p.name));

                const heldChart = await initOne('fiHeldChart', 'fiHeld', () => {
                    const names = Object.keys(heldDist);
                    const order = ['新买入', '短期', '中期', '长期'];
                    names.sort((a, b) => order.indexOf(a) - order.indexOf(b));
                    return {
                        tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                        legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                        series: [{
                            type: 'pie',
                            radius: ['45%', '70%'],
                            center: ['50%', '45%'],
                            data: names.map(n => ({ name: n, value: heldDist[n] })),
                            label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                        }]
                    };
                });
                if (heldChart) heldChart.on('click', (p) => openGroup(p.name, (x) => x.held_bucket === p.name));

                const retChart = await initOne('fiRetChart', 'fiRet', () => {
                    const buckets = [
                        { key: 'n10', label: '亏损>10%', min: -Infinity, max: -10 },
                        { key: 'n5', label: '亏损0~10%', min: -10, max: 0 },
                        { key: 'p5', label: '盈利0~5%', min: 0, max: 5 },
                        { key: 'p15', label: '盈利5~15%', min: 5, max: 15 },
                        { key: 'p25', label: '盈利15~25%', min: 15, max: 25 },
                        { key: 'p25p', label: '盈利>25%', min: 25, max: Infinity }
                    ].map(b => ({ ...b, value: 0, list: [] }));
                    const totalAmt = ctx.fiData.total_amount || 1;
                    products.forEach(p => {
                        const b = buckets.find(x => p.annual_return >= x.min && p.annual_return < x.max);
                        if (b) { b.value += p.amount_cny; b.list.push(p); }
                    });
                    const bucketTip = (b) => {
                        const items = b.list.slice().sort((a, x) => (x.amount_cny || 0) - (a.amount_cny || 0)).slice(0, 8)
                            .map(p => `· ${(p.name || '').slice(0, 14)} ¥${((p.amount_cny || 0) / 10000).toFixed(1)}万`).join('<br>');
                        const more = b.list.length > 8 ? `<br>… 等 ${b.list.length} 个产品` : '';
                        return `${b.label}<br>金额 ${(b.value / 10000).toFixed(1)}万 · 占比 ${(b.value / totalAmt * 100).toFixed(1)}%${items ? '<br>' + items : ''}${more}`;
                    };
                    return {
                        tooltip: { confine: true, trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (ps) => {
                            const b = buckets[ps[0].dataIndex];
                            return bucketTip(b);
                        } },
                        grid: { left: 50, right: 20, top: 20, bottom: 30 },
                        xAxis: { type: 'category', data: buckets.map(b => b.label), axisLabel: { color: '#888' } },
                        yAxis: { type: 'value', axisLabel: { color: '#888', formatter: (v) => (v / 10000).toFixed(1) + '万' } },
                        series: [{
                            type: 'bar',
                            barWidth: isMobile ? '60%' : 'auto',
                            data: buckets.map((b, i) => ({
                                value: b.value,
                                itemStyle: { color: ['#008a4a', '#66bb6a', '#aed581', '#ffb07a', '#ff5252', '#d32f2f'][i] }
                            })),
                            label: { show: true, position: 'top', color: '#aaa', fontSize: 11, formatter: (p) => (p.value > 0 ? ((p.value / 10000).toFixed(1) + '万') : '') }
                        }]
                    };
                });
                if (retChart) retChart.on('click', (p) => {
                    const bucket = [
                        { label: '亏损>10%', min: -Infinity, max: -10 },
                        { label: '亏损0~10%', min: -10, max: 0 },
                        { label: '盈利0~5%', min: 0, max: 5 },
                        { label: '盈利5~15%', min: 5, max: 15 },
                        { label: '盈利15~25%', min: 15, max: 25 },
                        { label: '盈利>25%', min: 25, max: Infinity }
                    ].find(b => b.label === p.name);
                    if (!bucket) return;
                    openGroup(p.name, (x) => x.annual_return !== null && x.annual_return !== undefined && x.annual_return >= bucket.min && x.annual_return < bucket.max);
                });
                }


                async function initRemainingCharts(charts, ctx) {
                const initOne = async (id, key, makeOption) => {
                    let el = document.getElementById(id);
                    const deadline = Date.now() + 8000;
                    while (!el && Date.now() < deadline) {
                        el = document.getElementById(id);
                        await new Promise(r => setTimeout(r, 100));
                    }
                    if (!el) return null;
                    if (charts[key]) { charts[key].dispose(); charts[key] = null; }
                    charts[key] = echarts.init(el);
                    charts[key].setOption(makeOption(), true);
                    return charts[key];
                };

                const catDist = (ctx.remData.categories || []).map(c => ({ name: c.name, value: c.amount }));
                const riskDist = ctx.remData.risk_distribution || {};
                const heldDist = ctx.remData.held_distribution || {};
                const products = ctx.remData.products || [];
                const isMobile = window.innerWidth <= 768;
                const openGroup = (name, filter) => {
                    const list = products.filter(filter);
                    if (!list.length) return;
                    ctx.openFiGroupDetail(`${name}（${list.length} 个）`, list);
                };

                const catChart = await initOne('remCatChart', 'remCat', () => ({
                    tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                    legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                    series: [{
                        type: 'pie',
                        radius: ['45%', '70%'],
                        center: ['50%', '45%'],
                        data: catDist,
                        label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                    }]
                }));
                if (catChart) catChart.on('click', (p) => openGroup(p.name, (x) => x.category === p.name));

                const riskChart = await initOne('remRiskChart', 'remRisk', () => {
                    const names = Object.keys(riskDist);
                    const order = ['低', '中低', '中', '中高', '高'];
                    names.sort((a, b) => order.indexOf(a) - order.indexOf(b));
                    return {
                        tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                        legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                        series: [{
                            type: 'pie',
                            radius: ['45%', '70%'],
                            center: ['50%', '45%'],
                            data: names.map(n => ({ name: n, value: riskDist[n] })),
                            label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                        }]
                    };
                });
                if (riskChart) riskChart.on('click', (p) => openGroup(p.name, (x) => x.risk_level === p.name));

                const heldChart = await initOne('remHeldChart', 'remHeld', () => {
                    const names = Object.keys(heldDist);
                    const order = ['新买入', '短期', '中期', '长期'];
                    names.sort((a, b) => order.indexOf(a) - order.indexOf(b));
                    return {
                        tooltip: { confine: true, trigger: 'item', formatter: (p) => `${p.name}：${(p.value / 10000).toFixed(1)}万 (${Number(p.percent).toFixed(2)}%)` },
                        legend: { textStyle: { color: '#aaa' }, bottom: 0 },
                        series: [{
                            type: 'pie',
                            radius: ['45%', '70%'],
                            center: ['50%', '45%'],
                            data: names.map(n => ({ name: n, value: heldDist[n] })),
                            label: { color: '#aaa', formatter: (p) => p.name + ': ' + Number(p.percent).toFixed(2) + '%' }
                        }]
                    };
                });
                if (heldChart) heldChart.on('click', (p) => openGroup(p.name, (x) => x.held_bucket === p.name));

                const retChart = await initOne('remRetChart', 'remRet', () => {
                    const buckets = [
                        { key: 'n10', label: '亏损>10%', min: -Infinity, max: -10 },
                        { key: 'n5', label: '亏损0~10%', min: -10, max: 0 },
                        { key: 'p5', label: '盈利0~5%', min: 0, max: 5 },
                        { key: 'p15', label: '盈利5~15%', min: 5, max: 15 },
                        { key: 'p25', label: '盈利15~25%', min: 15, max: 25 },
                        { key: 'p25p', label: '盈利>25%', min: 25, max: Infinity }
                    ].map(b => ({ ...b, value: 0, list: [] }));
                    const totalAmt = ctx.remData.total_amount || 1;
                    products.forEach(p => {
                        const r = p.annual_return;
                        if (r === null || r === undefined) return;
                        const b = buckets.find(x => r >= x.min && r < x.max);
                        if (b) { b.value += p.amount_cny; b.list.push(p); }
                    });
                    const bucketTip = (b) => {
                        const items = b.list.slice().sort((a, x) => (x.amount_cny || 0) - (a.amount_cny || 0)).slice(0, 8)
                            .map(p => `· ${(p.name || '').slice(0, 14)} ¥${((p.amount_cny || 0) / 10000).toFixed(1)}万`).join('<br>');
                        const more = b.list.length > 8 ? `<br>… 等 ${b.list.length} 个产品` : '';
                        return `${b.label}<br>金额 ${(b.value / 10000).toFixed(1)}万 · 占比 ${(b.value / totalAmt * 100).toFixed(1)}%${items ? '<br>' + items : ''}${more}`;
                    };
                    return {
                        tooltip: { confine: true, trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (ps) => {
                            const b = buckets[ps[0].dataIndex];
                            return bucketTip(b);
                        } },
                        grid: { left: 50, right: 20, top: 20, bottom: 30 },
                        xAxis: { type: 'category', data: buckets.map(b => b.label), axisLabel: { color: '#888' } },
                        yAxis: { type: 'value', axisLabel: { color: '#888', formatter: (v) => (v / 10000).toFixed(1) + '万' } },
                        series: [{
                            type: 'bar',
                            barWidth: isMobile ? '60%' : 'auto',
                            data: buckets.map((b, i) => ({
                                value: b.value,
                                itemStyle: { color: ['#008a4a', '#66bb6a', '#aed581', '#ffb07a', '#ff5252', '#d32f2f'][i] }
                            })),
                            label: { show: true, position: 'top', color: '#aaa', fontSize: 11, formatter: (p) => (p.value > 0 ? ((p.value / 10000).toFixed(1) + '万') : '') }
                        }]
                    };
                });
                if (retChart) retChart.on('click', (p) => {
                    const bucket = [
                        { label: '亏损>10%', min: -Infinity, max: -10 },
                        { label: '亏损0~10%', min: -10, max: 0 },
                        { label: '盈利0~5%', min: 0, max: 5 },
                        { label: '盈利5~15%', min: 5, max: 15 },
                        { label: '盈利15~25%', min: 15, max: 25 },
                        { label: '盈利>25%', min: 25, max: Infinity }
                    ].find(b => b.label === p.name);
                    if (!bucket) return;
                    openGroup(p.name, (x) => x.annual_return !== null && x.annual_return !== undefined && x.annual_return >= bucket.min && x.annual_return < bucket.max);
                });
                }


                async function initTrendCharts(charts, ctx) {
                const initOne = async (id, key, makeOption) => {
                    let el = document.getElementById(id);
                    const deadline = Date.now() + 8000;
                    while (!el && Date.now() < deadline) {
                        el = document.getElementById(id);
                        await new Promise(r => setTimeout(r, 100));
                    }
                    if (!el) return null;
                    if (charts[key]) { charts[key].dispose(); charts[key] = null; }
                    charts[key] = echarts.init(el);
                    charts[key].setOption(makeOption(), true);
                    return charts[key];
                };

                const dates = ctx.trendData.dates || [];
                const total = ctx.trendData.total || [];
                const benchmarks = ctx.trendData.benchmarks || {};

                await initOne('trendMainChart', 'trendMain', () => {
                    const series = [{
                        name: '总资产（万元）',
                        type: 'line',
                        yAxisIndex: 0,
                        data: total,
                        smooth: true,
                        symbol: 'none',
                        itemStyle: { color: '#4fc3f7' },
                        lineStyle: { width: 2.5, color: '#4fc3f7' },
                        areaStyle: { color: 'rgba(79,195,247,0.12)' },
                        tooltip: { valueFormatter: (v) => v.toFixed(1) + ' 万' }
                    }];
                    const benchColors = { '沪深300': '#ff7043', '标普500': '#f06292', '黄金GLD': '#ffd54f' };
                    Object.keys(benchmarks).forEach((name, i) => {
                        const b = benchmarks[name];
                        const data = new Array(b.start_index).fill(null).concat(b.normalized);
                        const color = benchColors[name] || ['#ff7043', '#f06292', '#ffd54f'][i % 3];
                        series.push({
                            name: name + '（基准）',
                            type: 'line',
                            yAxisIndex: 1,
                            data,
                            smooth: true,
                            symbol: 'none',
                            itemStyle: { color },
                            lineStyle: { width: 2, type: 'dashed', color }
                        });
                    });
                    return {
                        tooltip: {
                            confine: true, trigger: 'axis',
                            formatter: (params) => params.map(p => {
                                if (p.seriesName === '总资产（万元）') return `${p.marker}${p.seriesName}：${Number(p.value).toFixed(1)} 万`;
                                return `${p.marker}${p.seriesName}：${Number(p.value).toFixed(1)}`;
                            }).join('<br>')
                        },
                        legend: { textStyle: { color: '#aaa' }, top: 0 },
                        grid: { left: 60, right: 60, top: 32, bottom: 50 },
                        xAxis: {
                            type: 'category',
                            data: dates,
                            axisLabel: { color: '#8899aa', fontSize: 10, interval: Math.floor(dates.length / 8) }
                        },
                        yAxis: [
                            { type: 'value', name: '万元', axisLabel: { color: '#8899aa', formatter: (v) => Number(v).toFixed(1) }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } } },
                            { type: 'value', name: '基准=100', min: 60, axisLabel: { color: '#8899aa' }, splitLine: { show: false } }
                        ],
                        series,
                        animation: false
                    };
                });

                await initOne('trendAcctChart', 'trendAcct', () => {
                    const acct = ctx.trendData.accounts || {};
                    const order = ['支付宝', '招商', '富途', '港招', '中金财富', '微信', '其他银行', '负债（信用卡/白条）'];
                    const palette = ['#4fc3f7', '#81c784', '#ffb74d', '#ba68c8', '#4db6ac', '#ff8a65', '#90a4ae', '#ef5350'];
                    const series = order.filter(n => acct[n]).map((n, i) => ({
                        name: n,
                        type: 'line',
                        stack: 'total',
                        areaStyle: { opacity: 0.7 },
                        symbol: 'none',
                        lineStyle: { width: 0.5, color: palette[i % palette.length] },
                        itemStyle: { color: palette[i % palette.length] },
                        data: acct[n],
                        emphasis: { focus: 'series' }
                    }));
                    return {
                        tooltip: {
                            confine: true, trigger: 'axis',
                            formatter: (params) => params[0].axisValue + '<br>' + params.map(p => `${p.marker}${p.seriesName}：${Number(p.value).toFixed(1)} 万`).join('<br>')
                        },
                        legend: { textStyle: { color: '#aaa' }, top: 0, type: 'scroll' },
                        grid: { left: 60, right: 20, top: 32, bottom: 50 },
                        xAxis: {
                            type: 'category',
                            data: dates,
                            axisLabel: { color: '#8899aa', fontSize: 10, interval: Math.floor(dates.length / 8) }
                        },
                        yAxis: { type: 'value', name: '万元', axisLabel: { color: '#8899aa', formatter: (v) => Number(v).toFixed(1) }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } } },
                        series,
                        animation: false
                    };
                });
                }


    async function initPortfolioConfigChart(charts, ctx) {
        const el = document.getElementById('portfolioConfigChart');
        if (!el) return;
        if (charts.portfolioConfig) { charts.portfolioConfig.dispose(); charts.portfolioConfig = null; }

        const total = ctx.summary && ctx.summary.total_assets ? ctx.summary.total_assets : 1;
        const remProds = (ctx.remData && ctx.remData.products) || [];
        const sumCat = (k) => remProds.filter(p => (p.category || '').includes(k)).reduce((a, p) => a + (p.amount_cny || 0), 0);
        const advice = (ctx.marketAdvice && ctx.marketAdvice.categories) || [];
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
            { name: '理财类', value: (ctx.wealthData && ctx.wealthData.total_amount) || 0, min: r1.min, max: r1.max },
            { name: '固收类', value: (ctx.fiData && ctx.fiData.total_amount) || 0, min: r2.min, max: r2.max },
            { name: '权益类', value: (ctx.equityData && ctx.equityData.total_amount) || 0, min: r3.min, max: r3.max },
            { name: '现金储备', value: sumCat('货币'), min: r4.min, max: r4.max },
            { name: '黄金', value: sumCat('黄金'), min: r5.min, max: r5.max },
            { name: '养老储备', value: sumCat('养老'), min: r6.min, max: r6.max }
        ].map(c => ({ ...c, pct: (c.value / total) * 100 }));

        const isMobile = window.innerWidth <= 768;
        charts.portfolioConfig = echarts.init(el);
        charts.portfolioConfig.setOption({
            tooltip: {
                confine: true,
                trigger: 'axis',
                axisPointer: { type: 'shadow' },
                formatter: (ps) => {
                    const c = cats[ps[0].dataIndex];
                    const lines = [`${c.name}：${c.pct.toFixed(1)}%（¥${(c.value / 10000).toFixed(1)}万）`,
                        `参考区间：${c.min}% ~ ${c.max}%`,
                        c.pct < c.min ? '⚠ 低于参考区间' : (c.pct > c.max ? '⚠ 高于参考区间' : '✓ 在参考区间内')];
                    return lines.join('<br>');
                }
            },
            legend: {
                data: ['当前占比', '参考区间'],
                textStyle: { color: '#888', fontSize: isMobile ? 10 : 12 },
                top: 0
            },
            grid: { left: 70, right: 40, top: 30, bottom: 20, containLabel: true },
            xAxis: {
                type: 'value',
                max: 100,
                axisLabel: { color: '#888', formatter: (v) => Number(v.toFixed(1)) + '%' },
                splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } }
            },
            yAxis: {
                type: 'category',
                data: cats.map(c => c.name),
                axisLabel: { color: '#aaa', fontSize: isMobile ? 11 : 13 },
                axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } }
            },
            series: [
                {
                    name: '参考区间',
                    type: 'bar',
                    barWidth: isMobile ? 22 : 28,
                    data: cats.map(c => ({
                        value: [c.min, c.max - c.min],
                        itemStyle: { color: 'rgba(0, 210, 255, 0.18)', borderRadius: [0, 4, 4, 0] },
                        tooltip: { show: false }
                    })),
                    stack: 'range'
                },
                {
                    name: '当前占比',
                    type: 'bar',
                    barWidth: isMobile ? 22 : 28,
                    data: cats.map(c => ({
                        value: c.pct,
                        itemStyle: {
                            color: (c.pct >= c.min && c.pct <= c.max) ? '#00c853' : '#ff9800',
                            borderRadius: [0, 4, 4, 0]
                        },
                        label: { show: true, position: 'right', color: '#aaa', fontSize: 11, formatter: (p) => Number(p.value).toFixed(2) + '%' }
                    })),
                    z: 5
                }
            ]
        }, true);
    }


    window.AssetCharts = {
        initAllocationChart,
        initProfitChart,
        initRiskChart,
        initWealthCharts,
        initEquityCharts,
        initFixedIncomeCharts,
        initRemainingCharts,
        initTrendCharts,
        initPortfolioConfigChart,
        handleResize,
        debounce,
    };
})();
