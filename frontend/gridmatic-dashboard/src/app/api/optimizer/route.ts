import { NextResponse } from "next/server";
import { BigQuery } from "@google-cloud/bigquery";

function getBigQueryClient(): BigQuery {
  const projectId = process.env.GCP_PROJECT;
  const saJson = process.env.GCP_SA_KEY_JSON;

  if (saJson && projectId) {
    try {
      const creds = JSON.parse(saJson);
      if (creds.private_key && typeof creds.private_key === "string") {
        creds.private_key = creds.private_key.replace(/\\n/g, "\n");
      }
      return new BigQuery({ projectId, credentials: creds });
    } catch (e) {
      console.error("Failed to parse GCP_SA_KEY_JSON, falling back to default auth", e);
    }
  }

  return new BigQuery({ projectId });
}

const client = getBigQueryClient();

export async function GET() {
  try {
    const [rows] = await client.query({
      query: `
        SELECT timestamp_hour, price, charge_mwh, discharge_mwh, soc_mwh, bid_mwh, expected_profit
        FROM \`${process.env.GCP_PROJECT}.${process.env.BQ_DATASET}.gold_optimizer_outputs\`
        WHERE timestamp_hour >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), HOUR)
        ORDER BY timestamp_hour
      `,
    });
    
    return NextResponse.json(rows);
  } catch (error) {
    console.error("Error fetching optimizer data:", error);
    return NextResponse.json(
      { error: "Failed to fetch optimizer data" },
      { status: 500 }
    );
  }
}
