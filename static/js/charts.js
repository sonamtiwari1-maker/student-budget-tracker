/* ===================================================================
   UniBudget - Chart.js Visualizations
   =================================================================== */

window.AppCharts = (function () {
  let doughnutChart = null;
  let trendChart = null;
  let budgetVsActualChart = null;
  let paymentMethodChart = null;

  // Chart theme colors helper
  function getThemeColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      textColor: isDark ? '#94a3b8' : '#64748b',
      gridColor: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.05)',
      cardBg: isDark ? '#131b2e' : '#ffffff',
    };
  }

  function initOrUpdateCategoryDoughnut(canvasId, categories, currency) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (doughnutChart) {
      doughnutChart.destroy();
    }

    const filtered = categories.filter(c => c.spent > 0);
    const labels = filtered.length > 0 ? filtered.map(c => `${c.icon} ${c.name}`) : ['No expenses yet'];
    const data = filtered.length > 0 ? filtered.map(c => c.spent) : [1];
    const colors = filtered.length > 0 ? filtered.map(c => c.color) : ['#cbd5e1'];

    const theme = getThemeColors();

    doughnutChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: theme.cardBg,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: {
              color: theme.textColor,
              font: { family: 'inherit', size: 11, weight: '600' },
              boxWidth: 12,
              padding: 10
            }
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                if (filtered.length === 0) return ' No spending recorded';
                const val = ctx.parsed || 0;
                return ` ${ctx.label}: ${currency}${val.toFixed(2)}`;
              }
            }
          }
        },
        cutout: '68%'
      }
    });
  }

  function initOrUpdateTrendChart(canvasId, dailyTrend, currency) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (trendChart) {
      trendChart.destroy();
    }

    const labels = dailyTrend.map(d => `Day ${d.day}`);
    const data = dailyTrend.map(d => d.amount);
    const theme = getThemeColors();

    trendChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Daily Spending',
          data: data,
          backgroundColor: '#4f46e5',
          borderRadius: 4,
          hoverBackgroundColor: '#6366f1'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              color: theme.textColor,
              font: { size: 10 },
              maxTicksLimit: 15
            }
          },
          y: {
            grid: { color: theme.gridColor },
            ticks: {
              color: theme.textColor,
              callback: function (val) { return `${currency}${val}`; }
            },
            beginAtZero: true
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                return ` Spent: ${currency}${ctx.parsed.y.toFixed(2)}`;
              }
            }
          }
        }
      }
    });
  }

  function initOrUpdateBudgetVsActual(canvasId, categories, currency) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (budgetVsActualChart) {
      budgetVsActualChart.destroy();
    }

    const theme = getThemeColors();
    const sorted = [...categories].sort((a, b) => b.budget_limit - a.budget_limit).slice(0, 7);

    const labels = sorted.map(c => `${c.icon} ${c.name}`);
    const actualData = sorted.map(c => c.spent);
    const budgetData = sorted.map(c => c.budget_limit);

    budgetVsActualChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Actual Spent',
            data: actualData,
            backgroundColor: sorted.map(c => c.spent > c.budget_limit ? '#ef4444' : '#10b981'),
            borderRadius: 4
          },
          {
            label: 'Budget Cap',
            data: budgetData,
            backgroundColor: theme.gridColor.replace('0.05', '0.2').replace('0.06', '0.2') || '#94a3b8',
            borderRadius: 4
          }
        ]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            grid: { color: theme.gridColor },
            ticks: {
              color: theme.textColor,
              callback: function (val) { return `${currency}${val}`; }
            },
            beginAtZero: true
          },
          y: {
            grid: { display: false },
            ticks: {
              color: theme.textColor,
              font: { size: 11, weight: '500' }
            }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: theme.textColor,
              font: { size: 11, weight: '600' }
            }
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                return ` ${ctx.dataset.label}: ${currency}${ctx.parsed.x.toFixed(2)}`;
              }
            }
          }
        }
      }
    });
  }

  function initOrUpdatePaymentMethods(canvasId, methods, currency) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (paymentMethodChart) {
      paymentMethodChart.destroy();
    }

    const theme = getThemeColors();
    const palette = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

    const labels = methods.length > 0 ? methods.map(m => m.method) : ['No transactions'];
    const data = methods.length > 0 ? methods.map(m => m.amount) : [1];
    const colors = methods.length > 0 ? palette.slice(0, methods.length) : ['#cbd5e1'];

    paymentMethodChart = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: theme.cardBg
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: {
              color: theme.textColor,
              font: { size: 11, weight: '600' },
              boxWidth: 12,
              padding: 10
            }
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                if (methods.length === 0) return ' No data';
                return ` ${ctx.label}: ${currency}${ctx.parsed.toFixed(2)}`;
              }
            }
          }
        }
      }
    });
  }

  function updateAll(summary) {
    const curr = summary.currency || '$';
    initOrUpdateCategoryDoughnut('categoryDoughnutChart', summary.categories || [], curr);
    initOrUpdateTrendChart('spendingTrendChart', summary.daily_trend || [], curr);
    initOrUpdateBudgetVsActual('budgetVsActualChart', summary.categories || [], curr);
    initOrUpdatePaymentMethods('paymentMethodChart', summary.payment_methods || [], curr);
  }

  return {
    updateAll
  };
})();
