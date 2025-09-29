import { NextResponse } from "next/server";
import { BigQuery } from "@google-cloud/bigquery";

function getBigQueryClient(): BigQuery {
  const projectId = process.env.GCP_PROJECT;
  const saJson = process.env.GCP_SA_KEY_JSON;

  if (saJson && projectId) {
    try {
      const creds = JSON.parse(saJson);
      // Some providers escape newlines in env vars; normalize
      if (creds.private_key && typeof creds.private_key === "string") {
        creds.private_key = creds.private_key.replace(/\\n/g, "\n");
      }
      return new BigQuery({ projectId, credentials: creds });
    } catch (e) {
      console.error("Failed to parse GCP_SA_KEY_JSON, falling back to default auth", e);
    }
  }

  // Fallback to ADC (GOOGLE_APPLICATION_CREDENTIALS or runtime default)
  return new BigQuery({ projectId });
}

const client = getBigQueryClient();

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
    
    // Transform BigQuery timestamp format to simple strings
    const transformedRows = rows.map((row: any) => ({
      timestamp_hour: row.timestamp_hour?.value || row.timestamp_hour,
      yhat: row.yhat,
      yhat_lower: row.yhat_lower,
      yhat_upper: row.yhat_upper
    }));
    
    return NextResponse.json(transformedRows);
  } catch (error) {
    console.error("Error fetching forecast data:", error);
    return NextResponse.json(
      { error: "Failed to fetch forecast data" },
      { status: 500 }
    );
  }
}
