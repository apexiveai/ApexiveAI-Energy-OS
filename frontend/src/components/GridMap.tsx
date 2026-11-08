
import { useCallback, useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Popup,
  CircleMarker,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import type { FeatureCollection, Feature, Geometry } from "geojson";
import {
  Activity,
  AlertTriangle,
  Building2,
  Cable,
  RefreshCw,
  MapPin,
  Layers,
  Wifi,
  WifiOff,
} from "lucide-react";
import "leaflet/dist/leaflet.css";
import "./GridMap.css";

const API_BASE = "http://127.0.0.1:8017/api/v1";

type GridProperties = {
  feature_type?: string;
  feature_code?: string;
  name?: string;
  region?: string;
  township?: string;
  voltage_kv?: number;
  capacity_mva?: number;
  line_type?: string;
  status?: string;
  [key: string]: unknown;
};

type GridFeature = Feature<Geometry, GridProperties>;

type GridCollection = FeatureCollection<Geometry, GridProperties> & {
  total_features?: number;
  data_source?: string;
};

const DEFAULT_CENTER: [number, number] = [16.8661, 96.1951];

function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getFeatureColor(type?: string) {
  switch (type) {
    case "substation":
      return "#60a5fa";
    case "transformer":
      return "#fbbf24";
    case "outage":
      return "#fb7185";
    case "distribution_line":
      return "#34d399";
    default:
      return "#a78bfa";
  }
}

function MapResizeHandler() {
  const map = useMap();

  useEffect(() => {
    const timer = window.setTimeout(() => {
      map.invalidateSize();
    }, 150);

    return () => window.clearTimeout(timer);
  }, [map]);

  return null;
}

export default function GridMap() {
  const [data, setData] = useState<GridCollection | null>(null);
  const [region, setRegion] = useState("All Regions");
  const [township, setTownship] = useState("All Townships");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  const loadMap = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams();

      if (region !== "All Regions") {
        params.set("region", region);
      }

      if (township !== "All Townships") {
        params.set("township", township);
      }

      const suffix = params.toString()
        ? `?${params.toString()}`
        : "";

      const response = await fetch(`${API_BASE}/gis/map${suffix}`);

      if (!response.ok) {
        throw new Error(`GIS API returned HTTP ${response.status}`);
      }

      const result = (await response.json()) as GridCollection;

      if (
        result.type !== "FeatureCollection" ||
        !Array.isArray(result.features)
      ) {
        throw new Error("Invalid GeoJSON FeatureCollection");
      }

      setData(result);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load GIS data"
      );
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [region, township]);

  useEffect(() => {
    void loadMap();
  }, [loadMap]);

  const features = data?.features ?? [];

  const countType = (type: string) =>
    features.filter(
      (feature) => feature.properties?.feature_type === type
    ).length;

  const regionOptions = [
    "All Regions",
    "Yangon",
    "Mandalay",
    "Naypyidaw",
    "Bago",
    "Ayeyarwady",
    "Sagaing",
    "Magway",
    "Tanintharyi",
    "Kachin",
    "Kayah",
    "Kayin",
    "Chin",
    "Mon",
    "Rakhine",
    "Shan",
  ];
  
  const townshipOptions = [
    "All Townships",
    ...Array.from(
      new Set(
        features
          .filter(
            (feature) =>
              region === "All Regions" ||
              feature.properties?.region === region
          )
          .map((feature) => feature.properties?.township)
          .filter((value): value is string => Boolean(value))
      )
    ),
  ];

  const onEachFeature = (
    feature: GridFeature,
    layer: L.Layer
  ) => {
    const properties = feature.properties ?? {};
    const type = escapeHtml(properties.feature_type);
    const name = escapeHtml(properties.name);
    const code = escapeHtml(properties.feature_code);
    const townshipName = escapeHtml(properties.township);
    const regionName = escapeHtml(properties.region);

    const extra =
      properties.voltage_kv !== undefined
        ? `<div>Voltage: ${escapeHtml(properties.voltage_kv)} kV</div>`
        : properties.capacity_mva !== undefined
          ? `<div>Capacity: ${escapeHtml(properties.capacity_mva)} MVA</div>`
          : properties.line_type
            ? `<div>Line: ${escapeHtml(properties.line_type)}</div>`
            : "";

    layer.bindPopup(`
      <div class="grid-popup">
        <div class="popup-type">${type.replaceAll("_", " ")}</div>
        <strong>${name}</strong>
        <div>Code: ${code}</div>
        <div>${townshipName}, ${regionName}</div>
        ${extra}
      </div>
    `);
  };

  const pointToLayer = (
    feature: GridFeature,
    latlng: L.LatLng
  ) => {
    const color = getFeatureColor(
      feature.properties?.feature_type
    );

    return L.circleMarker(latlng, {
      radius: 9,
      color,
      weight: 2,
      fillColor: color,
      fillOpacity: 0.85,
    });
  };

  const styleFeature = (feature?: GridFeature) => {
    const type = feature?.properties?.feature_type;

    return {
      color: getFeatureColor(type),
      weight: type === "distribution_line" ? 5 : 3,
      opacity: 0.9,
    };
  };

  return (
    <div className="gis-page">
      <div className="gis-toolbar">
        <div className="gis-toolbar-title">
          <div className="gis-title-icon">
            <Layers size={19} />
          </div>
          <div>
            <h2>National Grid Network</h2>
            <p>Geospatial infrastructure monitoring</p>
          </div>
        </div>

        <div className="gis-toolbar-actions">
          <select
            value={region}
            onChange={(event) => {
              setRegion(event.target.value);
              setTownship("All Townships");
            }}
          >
            {regionOptions.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>

          <select
            value={township}
            onChange={(event) => setTownship(event.target.value)}
          >
            {townshipOptions.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>

          <button
            className="gis-refresh"
            onClick={() => void loadMap()}
            disabled={loading}
          >
            <RefreshCw
              size={15}
              className={loading ? "spinning" : ""}
            />
            Refresh
          </button>
        </div>
      </div>

      <div className="gis-stats">
        <div className="gis-stat">
          <span className="gis-stat-icon blue"><Building2 size={18}/></span>
          <div>
            <small>SUBSTATIONS</small>
            <strong>{countType("substation")}</strong>
          </div>
        </div>

        <div className="gis-stat">
          <span className="gis-stat-icon yellow"><Activity size={18}/></span>
          <div>
            <small>TRANSFORMERS</small>
            <strong>{countType("transformer")}</strong>
          </div>
        </div>

        <div className="gis-stat">
          <span className="gis-stat-icon green"><Cable size={18}/></span>
          <div>
            <small>DISTRIBUTION LINES</small>
            <strong>{countType("distribution_line")}</strong>
          </div>
        </div>

        <div className="gis-stat">
          <span className="gis-stat-icon red"><AlertTriangle size={18}/></span>
          <div>
            <small>OUTAGE LOCATIONS</small>
            <strong>{countType("outage")}</strong>
          </div>
        </div>
      </div>

      <div className="gis-map-panel">
        <div className="gis-map-heading">
          <div>
            <strong>
              <MapPin size={15}/> Geographic Grid View
            </strong>
            <span>
              {data?.total_features ?? features.length} mapped features
            </span>
          </div>

          <div className="gis-connection">
            {error ? (
              <>
                <WifiOff size={14}/>
                API DISCONNECTED
              </>
            ) : (
              <>
                <Wifi size={14}/>
                POSTGRESQL GIS
              </>
            )}
          </div>
        </div>

        {error && (
          <div className="gis-error">
            <WifiOff size={17}/>
            <div>
              <strong>Unable to load grid map</strong>
              <span>{error}. Check that the FastAPI backend is running.</span>
            </div>
            <button onClick={() => void loadMap()}>Retry</button>
          </div>
        )}

        <div className="gis-map">
          <MapContainer
            center={DEFAULT_CENTER}
            zoom={13}
            scrollWheelZoom
            className="leaflet-map"
          >
            <MapResizeHandler />

            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {data && (
              <GeoJSON
                key={`${region}-${township}-${lastUpdated}`}
                data={data as FeatureCollection}
                pointToLayer={(feature, latlng) =>
                  pointToLayer(feature as GridFeature, latlng)
                }
                style={(feature) =>
                  styleFeature(feature as GridFeature)
                }
                onEachFeature={(feature, layer) =>
                  onEachFeature(feature as GridFeature, layer)
                }
              />
            )}

            {!data && !error && (
              <CircleMarker
                center={DEFAULT_CENTER}
                radius={8}
                pathOptions={{
                  color: "#60a5fa",
                  fillColor: "#60a5fa",
                  fillOpacity: 0.8,
                }}
              >
                <Popup>Yangon Demo Map Center</Popup>
              </CircleMarker>
            )}
          </MapContainer>

          {loading && (
            <div className="gis-loading">
              <RefreshCw size={17} className="spinning"/>
              Loading grid data...
            </div>
          )}

          <div className="gis-legend">
            <strong>MAP LEGEND</strong>
            <span><i className="legend-substation"/> Substation</span>
            <span><i className="legend-transformer"/> Transformer</span>
            <span><i className="legend-line"/> Distribution Line</span>
            <span><i className="legend-outage"/> Outage</span>
          </div>
        </div>

        <div className="gis-map-footer">
          <span>Data: {data?.data_source ?? "Waiting for API"}</span>
          <span>Last updated: {lastUpdated || "—"}</span>
          <span>Coordinate system: WGS84 / EPSG:4326</span>
        </div>
      </div>

      <div className="gis-disclaimer">
        DEMO GIS DATA — NOT A LIVE EPC NETWORK. Map tiles require an internet connection.
      </div>
    </div>
  );
}
