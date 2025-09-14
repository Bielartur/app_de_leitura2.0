/**
 * Gráfico de barras com degradê (tema claro).
 * @param {string|HTMLElement} el
 * @param categories:string[], data:number[], title?:string, colorFrom?:string, colorTo?:string opts
 */
function renderBarChartGradient(el, {
    categories,
    data,
    title = '',
    colorFrom = '#F59E0B', // amber-500
    colorTo = '#EF4444'  // red-500
}) {
    const target = typeof el === 'string' ? document.querySelector(el) : el;

    const options = {
        chart: {type: 'bar', height: 260, toolbar: {show: false}, background: 'transparent'},
        theme: {mode: 'light'},
        series: [{name: title || 'Série', data}],
        colors: [colorFrom],
        xaxis: {
            categories,
            axisBorder: {show: false},
            axisTicks: {show: false},
            labels: {
                formatter: (value) => value // padrão = mostra tudo
            }
        },
        yaxis: {labels: {formatter: v => v.toLocaleString('pt-BR')}},
        plotOptions: {
            bar: {
                borderRadius: 4,
                columnWidth: '75%',
                dataLabels: {position: 'top'}
            }
        },
        dataLabels: {
            enabled: true,
            formatter: v => v,
            offsetY: -20,
            style: {fontSize: '12px'}
        },
        grid: {strokeDashArray: 4},
        tooltip: {theme: 'light'},
        fill: {
            type: 'gradient',
            gradient: {
                type: 'vertical',
                shade: 'light',
                shadeIntensity: 0.2,
                gradientToColors: [colorTo],
                opacityFrom: 0.95,
                opacityTo: 0.85,
                stops: [0, 100]
            }
        },
        title: title ? {text: title, style: {fontWeight: 600}} : undefined,

        // <<< Ajuste responsivo >>>
        responsive: [
            {
                breakpoint: 768, // md do Tailwind
                options: {
                    xaxis: {
                        labels: {
                            formatter: (value) => {
                                // mostra só números pares
                                return parseInt(value) % 2 === 0 ? value : '';
                            }
                        }
                    }
                }
            }
        ]
    };

    const chart = new ApexCharts(target, options);
    chart.render();
    return chart;
}

// pega o dict que veio do Django
const diario = JSON.parse(document.getElementById('diario-json').textContent);

// ordena as datas (YYYY-MM-DD) pra ficar certinho
const orderedDates = Object.keys(diario).sort();

// labels = dia do mês ("01", "02", ...)
const labels = orderedDates.map(d => d.slice(8));

// values = páginas lidas naquele dia (já vem com zeros se você preencheu no backend)
const values = orderedDates.map(d => diario[d] ?? 0);

// Exemplo de uso
const categories = labels;
const data = values;

const chart = renderBarChartGradient('#bar-chart', {
    title: ' ',
    categories,
    data,
    colorFrom: 'hsl(252, 46%, 33%)',
    colorTo: 'hsl(186, 80%, 35%)'
});