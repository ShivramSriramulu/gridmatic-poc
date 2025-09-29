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
  Legend
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
        <h2 className="text-lg font-medium mb-4">Battery Optimization</h2>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-lg font-medium mb-4">Battery Optimization</h2>
        <div className="text-red-600 text-center py-8">
          Error: {error}
        </div>
      </div>
    );
  }

  const labels = rows.map(r => new Date(r.timestamp_hour).toLocaleString());
  const charge = rows.map(r => r.charge_mwh);
  const discharge = rows.map(r => -r.discharge_mwh);
  const soc = rows.map(r => r.soc_mwh);

  const chartData = {
    labels,
    datasets: [
      {
        label: "Charge",
        data: charge,
        backgroundColor: "rgba(34, 197, 94, 0.7)",
        borderColor: "rgba(34, 197, 94, 1)",
        borderWidth: 1,
      },
      {
        label: "Discharge",
        data: discharge,
        backgroundColor: "rgba(239, 68, 68, 0.7)",
        borderColor: "rgba(239, 68, 68, 1)",
        borderWidth: 1,
      },
    ],
  };

  const socData = {
    labels,
    datasets: [
      {
        label: "SoC",
        data: soc,
        borderColor: "rgba(147, 51, 234, 1)",
        backgroundColor: "rgba(147, 51, 234, 0.1)",
        fill: true,
        tension: 0.1,
      },
    ],
  };

  const barOptions = {
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
          text: "Power (MW)",
        },
      },
    },
  };

  const lineOptions = {
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
          text: "SoC (MWh)",
        },
      },
    },
  };

  const totalProfit = rows.reduce((sum, row) => sum + row.expected_profit, 0);
  const avgSoc = rows.reduce((sum, row) => sum + row.soc_mwh, 0) / rows.length;
  const totalCharge = rows.reduce((sum, row) => sum + row.charge_mwh, 0);
  const totalDischarge = rows.reduce((sum, row) => sum + row.discharge_mwh, 0);

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-lg font-medium mb-4">Battery Optimization</h2>
      <div className="space-y-6">
        <div className="h-64">
          <Bar data={chartData} options={barOptions} />
        </div>
        <div className="h-48">
          <Line data={socData} options={lineOptions} />
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div className="bg-green-50 p-3 rounded">
          <div className="text-green-800 font-medium">Total Charge</div>
          <div className="text-green-600">{totalCharge.toFixed(1)} MWh</div>
        </div>
        <div className="bg-red-50 p-3 rounded">
          <div className="text-red-800 font-medium">Total Discharge</div>
          <div className="text-red-600">{totalDischarge.toFixed(1)} MWh</div>
        </div>
        <div className="bg-purple-50 p-3 rounded">
          <div className="text-purple-800 font-medium">Avg SoC</div>
          <div className="text-purple-600">{avgSoc.toFixed(1)} MWh</div>
        </div>
        <div className="bg-blue-50 p-3 rounded">
          <div className="text-blue-800 font-medium">Expected Profit</div>
          <div className="text-blue-600">${(totalProfit / 1e12).toFixed(2)}T</div>
        </div>
      </div>
      <div className="mt-4 text-sm text-gray-600">
        <p>📊 Data points: {rows.length}</p>
        <p>🔄 Auto-refresh: Every 5 minutes</p>
      </div>
    </div>
  );
}
