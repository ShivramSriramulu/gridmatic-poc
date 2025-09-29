"use client";
import { Bar, Line } from "react-chartjs-2";
import { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
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
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

type OptRow = { 
  timestamp_hour: string; 
  price: number;
  charge_mwh: number; 
  discharge_mwh: number; 
  soc_mwh: number;
  bid_mwh: number;
  expected_profit: number;
};

export default function BatteryChart() {
  const [rows, setRows] = useState<OptRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("/api/optimizer");
        if (!response.ok) {
          throw new Error("Failed to fetch optimizer data");
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
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 px-6 py-4 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Battery Optimization</h2>
                <p className="text-sm text-gray-600">CVXPY-based dispatch optimization</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Loading...</span>
            </div>
          </div>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-center h-80">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading optimization data...</p>
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
              <h2 className="text-xl font-semibold text-gray-900">Battery Optimization</h2>
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
  const charge = rows.map(r => r.charge_mwh);
  const discharge = rows.map(r => -r.discharge_mwh);
  const soc = rows.map(r => r.soc_mwh);
  const price = rows.map(r => r.price);

  const chartData = {
    labels,
    datasets: [
      {
        label: "Charge",
        data: charge,
        backgroundColor: "rgba(34, 197, 94, 0.8)",
        borderColor: "rgba(34, 197, 94, 1)",
        borderWidth: 1,
        borderRadius: 4,
        borderSkipped: false,
      },
      {
        label: "Discharge",
        data: discharge,
        backgroundColor: "rgba(239, 68, 68, 0.8)",
        borderColor: "rgba(239, 68, 68, 1)",
        borderWidth: 1,
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  };

  const socData = {
    labels,
    datasets: [
      {
        label: "State of Charge",
        data: soc,
        borderColor: "rgba(147, 51, 234, 1)",
        backgroundColor: "rgba(147, 51, 234, 0.1)",
        fill: true,
        tension: 0.1,
        pointRadius: 3,
        pointHoverRadius: 6,
        borderWidth: 3,
      },
    ],
  };

  const barOptions = {
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
        borderColor: 'rgba(34, 197, 94, 0.5)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: function(context: any) {
            const value = Math.abs(context.parsed.y);
            return `${context.dataset.label}: ${value.toFixed(1)} MW`;
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
          text: "Power (MW)",
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
            return Math.abs(value).toFixed(0) + ' MW';
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

  const lineOptions = {
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
        borderColor: 'rgba(147, 51, 234, 0.5)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)} MWh`;
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
          text: "SoC (MWh)",
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
            return value.toFixed(0) + ' MWh';
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

  // Calculate metrics
  const totalProfit = rows.reduce((sum, row) => sum + row.expected_profit, 0);
  const avgSoc = rows.length > 0 ? rows.reduce((sum, row) => sum + row.soc_mwh, 0) / rows.length : 0;
  const totalCharge = rows.reduce((sum, row) => sum + row.charge_mwh, 0);
  const totalDischarge = rows.reduce((sum, row) => sum + row.discharge_mwh, 0);
  const avgPrice = rows.length > 0 ? rows.reduce((sum, row) => sum + row.price, 0) / rows.length : 0;

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 px-6 py-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Battery Optimization</h2>
              <p className="text-sm text-gray-600">CVXPY-based dispatch optimization</p>
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

      {/* Metrics Cards */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-100">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-xl font-bold text-green-600">{totalCharge.toFixed(1)}</div>
            <div className="text-xs text-gray-600 uppercase tracking-wide">Total Charge (MWh)</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-red-600">{totalDischarge.toFixed(1)}</div>
            <div className="text-xs text-gray-600 uppercase tracking-wide">Total Discharge (MWh)</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-purple-600">{avgSoc.toFixed(1)}</div>
            <div className="text-xs text-gray-600 uppercase tracking-wide">Avg SoC (MWh)</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-blue-600">${totalProfit.toFixed(0)}</div>
            <div className="text-xs text-gray-600 uppercase tracking-wide">Expected Profit</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="p-6 space-y-6">
        {/* Power Chart */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">Charge/Discharge Operations</h3>
          <div className="h-64">
            <Bar data={chartData} options={barOptions} />
          </div>
        </div>

        {/* SOC Chart */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">Battery State of Charge</h3>
          <div className="h-48">
            <Line data={socData} options={lineOptions} />
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span>📊 Data points: {rows.length}</span>
            <span>💰 Avg Price: ${avgPrice.toFixed(2)}/MWh</span>
            <span>⚡ Efficiency: {((totalDischarge / totalCharge) * 100).toFixed(1)}%</span>
          </div>
          <span>🔄 Auto-refresh: Every 5 minutes</span>
        </div>
      </div>
    </div>
  );
}
