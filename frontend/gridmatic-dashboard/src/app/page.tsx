import TradingChart from "@/components/TradingChart";
import BatteryChart from "@/components/BatteryChart";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="inline-flex items-center space-x-3 mb-4">
            <div className="p-3 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-blue-900 bg-clip-text text-transparent">
              Gridmatic ERCOT POC Dashboard
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Real-time energy forecasting and battery optimization analytics powered by Prophet, CVXPY, and Google BigQuery
          </p>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white/80 backdrop-blur-sm p-6 rounded-xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-r from-blue-100 to-blue-200 rounded-xl">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-semibold text-gray-900">Prophet Forecasting</h3>
                <p className="text-sm text-gray-600">48-hour demand prediction with uncertainty bands</p>
              </div>
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm p-6 rounded-xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-r from-green-100 to-green-200 rounded-xl">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-semibold text-gray-900">CVXPY Optimization</h3>
                <p className="text-sm text-gray-600">Convex optimization for battery dispatch</p>
              </div>
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm p-6 rounded-xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-r from-purple-100 to-purple-200 rounded-xl">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-semibold text-gray-900">Real-time Data</h3>
                <p className="text-sm text-gray-600">Live BigQuery integration with auto-refresh</p>
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="space-y-8">
          <TradingChart />
          <BatteryChart />
        </div>

        {/* Footer */}
        <div className="mt-12 text-center">
          <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-center space-x-2 mb-3">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-gray-700">System Status: Operational</span>
            </div>
            <p className="text-sm text-gray-600 mb-2">
              <strong>Gridmatic ERCOT Proof of Concept</strong> • Powered by Google BigQuery & Next.js
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-gray-500">
              <span className="flex items-center space-x-1">
                <span className="w-1 h-1 bg-blue-500 rounded-full"></span>
                <span>EIA API (ERCOT)</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="w-1 h-1 bg-green-500 rounded-full"></span>
                <span>NOAA (Weather)</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="w-1 h-1 bg-purple-500 rounded-full"></span>
                <span>Prophet (Forecasting)</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="w-1 h-1 bg-orange-500 rounded-full"></span>
                <span>CVXPY (Optimization)</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}