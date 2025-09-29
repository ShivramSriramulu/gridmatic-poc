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
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-lg font-medium mb-4">Trading Forecast (48h)</h2>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-lg font-medium mb-4">Trading Forecast (48h)</h2>
        <div className="text-red-600 text-center py-8">
          Error: {error}
        </div>
      </div>
    );
  }

  const labels = rows.map(r => new Date(r.timestamp_hour).toLocaleString());
  const yhat = rows.map(r => r.yhat);
  const ylow = rows.map(r => r.yhat_lower);
  const yhigh = rows.map(r => r.yhat_upper);

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
      },
      {
        label: "Confidence Interval",
        data: yhigh,
        borderColor: "transparent",
        backgroundColor: "rgba(59, 130, 246, 0.2)",
        fill: "+1",
        pointRadius: 0,
      },
      {
        label: "_lower",
        data: ylow,
        borderColor: "transparent",
        backgroundColor: "rgba(59, 130, 246, 0.2)",
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
      },
      title: {
        display: false,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: "Time",
        },
      },
      y: {
        title: {
          display: true,
          text: "Demand (MW)",
        },
      },
    },
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-lg font-medium mb-4">Trading Forecast (48h)</h2>
      <div className="h-64">
        <Line data={chartData} options={options} />
      </div>
      <div className="mt-4 text-sm text-gray-600">
        <p>📊 Data points: {rows.length}</p>
        <p>📈 Forecast range: {Math.min(...yhat).toFixed(0)} - {Math.max(...yhat).toFixed(0)} MW</p>
        <p>🔄 Auto-refresh: Every 5 minutes</p>
      </div>
    </div>
  );
}
