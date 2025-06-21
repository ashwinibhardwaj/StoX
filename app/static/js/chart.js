$(document).ready(function () {
        var mobileFontSize = window.innerWidth < 768 ? 10 : 12;
        var mobileLegendBoxWidth = window.innerWidth < 768 ? 10 : 20;
        
        let priceTrendChart, volumeChart, ohlcChart;
        let priceChart, rsiChart, macdChart;
        
        $.getJSON('/get_tickers', function (tickers) {
          let tickerDropdown = $("#ticker-select");
          if (tickers.length > 0) {
            tickers.forEach(ticker => {
              tickerDropdown.append(new Option(ticker, ticker));
            });
            loadStockData(tickers[0]);
          } else {
            tickerDropdown.append(new Option("No tickers subscribed", ""));
          }
        });
        
        function populateStatsTable(stats) {
          let tbody = $("#stats-table tbody");
          tbody.empty();
          for (let key in stats) {
            let formattedKey = key.replace("_", " ").toUpperCase();
            tbody.append(`<tr><td>${formattedKey}</td><td>${stats[key]}</td></tr>`);
          }
        }
        
        function populateInsights(insights) {
          let ul = $("#insights-list");
          ul.empty();
          if (insights.length === 0) {
            ul.append("<li>No insights available at the moment.</li>");
          } else {
            insights.forEach(insight => {
              ul.append(`<li>${insight}</li>`);
            });
          }
        }
        
        function loadStockData(ticker) {
          if (!ticker) return;
          let selectedRange = $("#range-select").val();
          $.getJSON(`/get_stock_data/${ticker}?range=${selectedRange}`, function (data) {
            if (data.error) {
              alert(data.error);
              return;
            }
            
            if (priceTrendChart) priceTrendChart.destroy();
            if (volumeChart) volumeChart.destroy();
            if (ohlcChart) ohlcChart.destroy();
            if (priceChart) priceChart.destroy();
            if (rsiChart) rsiChart.destroy();
            if (macdChart) macdChart.destroy();
            
            let ctx1 = document.getElementById("priceTrendChart").getContext("2d");
            priceTrendChart = new Chart(ctx1, {
              type: "line",
              data: {
                labels: data.dates,
                datasets: [{
                  label: "Closing Price",
                  data: data.prices,
                  borderColor: "blue",
                  fill: false
                }]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: { labels: { fontSize: mobileFontSize, boxWidth: mobileLegendBoxWidth } },
                scales: {
                  x: { ticks: { fontSize: mobileFontSize } },
                  y: { ticks: { fontSize: mobileFontSize } }
                }
              }
            });
            
            let ctx2 = document.getElementById("volumeChart").getContext("2d");
            volumeChart = new Chart(ctx2, {
              type: "bar",
              data: {
                labels: data.dates,
                datasets: [{
                  label: "Trading Volume",
                  data: data.volume,
                  backgroundColor: "green"
                }]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: { labels: { fontSize: mobileFontSize, boxWidth: mobileLegendBoxWidth } },
                scales: {
                  x: { ticks: { fontSize: mobileFontSize } },
                  y: { ticks: { fontSize: mobileFontSize } }
                }
              }
            });
            
            let ctx3 = document.getElementById("ohlcChart").getContext("2d");
            ohlcChart = new Chart(ctx3, {
              type: "line",
              data: {
                labels: data.dates,
                datasets: [
                  { label: "Open", data: data.open, borderColor: "orange", fill: false },
                  { label: "High", data: data.high, borderColor: "red", fill: false },
                  { label: "Low", data: data.low, borderColor: "purple", fill: false },
                  { label: "Close", data: data.close, borderColor: "blue", fill: false }
                ]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: { labels: { fontSize: mobileFontSize, boxWidth: mobileLegendBoxWidth } },
                scales: {
                  x: { ticks: { fontSize: mobileFontSize } },
                  y: { ticks: { fontSize: mobileFontSize } }
                }
              }
            });
            
            let ctx4 = document.getElementById("priceChart").getContext("2d");
            priceChart = new Chart(ctx4, {
              type: "line",
              data: {
                labels: data.dates,
                datasets: [
                  { label: "Close", data: data.prices, borderColor: "blue", fill: false },
                  { label: "SMA20", data: data.SMA20, borderColor: "green", fill: false },
                  { label: "SMA50", data: data.SMA50, borderColor: "red", fill: false },
                  { label: "BB Upper", data: data.BB_upper, borderColor: "gray", borderDash: [5, 5], fill: false },
                  { label: "BB Lower", data: data.BB_lower, borderColor: "gray", borderDash: [5, 5], fill: false }
                ]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: { labels: { fontSize: mobileFontSize, boxWidth: mobileLegendBoxWidth } },
                scales: {
                  x: { ticks: { fontSize: mobileFontSize } },
                  y: { ticks: { fontSize: mobileFontSize } }
                }
              }
            });
            
            let ctx5 = document.getElementById("rsiChart").getContext("2d");
            rsiChart = new Chart(ctx5, {
              type: "line",
              data: {
                labels: data.dates,
                datasets: [{
                  label: "RSI",
                  data: data.RSI,
                  borderColor: "purple",
                  fill: false
                }]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: { labels: { fontSize: mobileFontSize, boxWidth: mobileLegendBoxWidth } },
                scales: {
                  x: { ticks: { fontSize: mobileFontSize } },
                  y: { ticks: { fontSize: mobileFontSize }, min: 0, max: 100 }
                }
              }
            });
            
            let ctx6 = document.getElementById("macdChart").getContext("2d");
            macdChart = new Chart(ctx6, {
              type: "line",
              data: {
                labels: data.dates,
                datasets: [
                  { label: "MACD", data: data.MACD, borderColor: "orange", fill: false },
                  { label: "Signal", data: data.MACD_signal, borderColor: "brown", fill: false }
                ]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: { labels: { fontSize: mobileFontSize, boxWidth: mobileLegendBoxWidth } },
                scales: {
                  x: { ticks: { fontSize: mobileFontSize } },
                  y: { ticks: { fontSize: mobileFontSize } }
                }
              }
            });
            
            let startDate = data.dates[0];
            let endDate = data.dates[data.dates.length - 1];
            $("#data-range").text(`Data range: ${startDate} to ${endDate}`);
            
            populateStatsTable(data.stats);
            populateInsights(data.insights);
            
          }).fail(function () {
            alert("Failed to fetch stock data.");
          });
        }
        
        $(document).on("change", "#ticker-select", function () {
          loadStockData($(this).val());
        });
    
        $(document).on("change", "#range-select", function () {
          loadStockData($("#ticker-select").val());
        });
      });