"use client";
import { Line } from "react-chartjs-2";
import { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

type FcRow = { 
  timestamp_hour: string; 
  yhat: number; 
  yhat_lower: number; 
  yhat_upper: number 
};

export default function TradingChart() {
  const [rows, setRows] = useState<FcRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("/api/forecast");
        if (!response.ok) {
          throw new Error("Failed to fetch forecast data");
        }
        const data = await response.json();
        setRows(data);
        setError(null);
        setLastUpdated(new Date());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Refresh every 5 minutes
    const interval = setInterval(fetchData, 300000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">ERCOT Demand Forecast</h2>
                <p className="text-sm text-gray-600">48-hour Prophet-based prediction</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span>Loading...</span>
            </div>
          </div>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-center h-80">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading forecast data...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="bg-gradient-to-r from-red-50 to-pink-50 px-6 py-4 border-b border-gray-100">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">ERCOT Demand Forecast</h2>
              <p className="text-sm text-gray-600">Error loading data</p>
            </div>
          </div>
        </div>
        <div className="p-6">
          <div className="text-center py-8">
            <div className="text-red-600 mb-2">
              <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-red-600 font-medium">Error: {error}</p>
            <p className="text-gray-500 text-sm mt-2">Please check your connection and try again</p>
          </div>
        </div>
      </div>
    );
  }

  const labels = rows.map(r => {
    // Handle BigQuery timestamp format
    const timestamp = r.timestamp_hour;
    if (!timestamp) return "Invalid Date";
    
    // Try parsing as ISO string first
    let date = new Date(timestamp);
    if (isNaN(date.getTime())) {
      // If that fails, try adding 'Z' for UTC
      date = new Date(timestamp + 'Z');
    }
    if (isNaN(date.getTime())) {
      // If still fails, try parsing as BigQuery format
      date = new Date(timestamp.replace(' ', 'T') + 'Z');
    }
    
    return isNaN(date.getTime()) ? "Invalid Date" : date.toLocaleString();
  });
  const yhat = rows.map(r => r.yhat);
  const ylow = rows.map(r => r.yhat_lower);
  const yhigh = rows.map(r => r.yhat_upper);

  // Calculate stats
  const avgDemand = rows.length > 0 ? (yhat.reduce((a, b) => a + b, 0) / yhat.length).toFixed(0) : 0;
  const maxDemand = rows.length > 0 ? Math.max(...yhat).toFixed(0) : 0;
  const minDemand = rows.length > 0 ? Math.min(...yhat).toFixed(0) : 0;

  const chartData = {
    labels,
    datasets: [
      {
        label: "Forecast",
        data: yhat,
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        fill: false,
        tension: 0.1,
        pointRadius: 3,
        pointHoverRadius: 6,
        borderWidth: 3,
      },
      {
        label: "Confidence Interval",
        data: yhigh,
        borderColor: "transparent",
        backgroundColor: "rgba(59, 130, 246, 0.15)",
        fill: "+1",
        pointRadius: 0,
      },
      {
        label: "_lower",
        data: ylow,
        borderColor: "transparent",
        backgroundColor: "rgba(59, 130, 246, 0.15)",
        fill: false,
        pointRadius: 0,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top" as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
            weight: '500'
          }
        }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(59, 130, 246, 0.5)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.parsed.y.toLocaleString()} MW`;
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: "Time",
          color: '#374151',
          font: {
            size: 12,
            weight: 'bold'
          }
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
          drawBorder: false
        },
        ticks: {
          color: '#6B7280',
          maxTicksLimit: 8,
          font: {
            size: 11
          }
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: "Demand (MW)",
          color: '#374151',
          font: {
            size: 12,
            weight: 'bold'
          }
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
          drawBorder: false
        },
        ticks: {
          color: '#6B7280',
          font: {
            size: 11
          },
          callback: function(value: any) {
            return value.toLocaleString() + ' MW';
          }
        }
      }
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">ERCOT Demand Forecast</h2>
              <p className="text-sm text-gray-600">48-hour Prophet-based prediction</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Live</span>
            {lastUpdated && (
              <span className="ml-2">Updated {lastUpdated.toLocaleTimeString()}</span>
            )}
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-100">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{avgDemand}</div>
            <div className="text-xs text-gray-600 uppercase tracking-wide">Avg Demand (MW)</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{maxDemand}</div>
            <div className="text-xs text-gray-600 uppercase tracking-wide">Peak Demand (MW)</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{minDemand}</div>
            <div className="text-xs text-gray-600 uppercase tracking-wide">Min Demand (MW)</div>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="p-6">
        <div className="h-80">
          <Line data={chartData} options={options} />
        </div>
      </div>

      {/* Footer Info */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span>📊 Data points: {rows.length}</span>
            <span>📈 Range: {minDemand} - {maxDemand} MW</span>
          </div>
          <span>🔄 Auto-refresh: Every 5 minutes</span>
        </div>
      </div>
    </div>
  );
}
