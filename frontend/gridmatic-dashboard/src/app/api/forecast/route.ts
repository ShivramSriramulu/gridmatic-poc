import { NextResponse } from "next/server";
import { BigQuery } from "@google-cloud/bigquery";

const client = new BigQuery({ projectId: process.env.GCP_PROJECT });

export async function GET() {
  try {
    const [rows] = await client.query({
      query: `
        SELECT timestamp_hour, yhat, yhat_lower, yhat_upper
        FROM \`${process.env.GCP_PROJECT}.${process.env.BQ_DATASET}.gold_forecasts\`
        WHERE timestamp_hour >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), HOUR)
        ORDER BY timestamp_hour
      `,
    });
    
    return NextResponse.json(rows);
  } catch (error) {
    console.error("Error fetching forecast data:", error);
    return NextResponse.json(
      { error: "Failed to fetch forecast data" },
      { status: 500 }
    );
  }
}
