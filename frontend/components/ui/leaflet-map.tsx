"use client";

import React, { useEffect } from "react";
import L from "leaflet";
import {
  MapContainer,
  TileLayer,
  Marker,
  CircleMarker,
  Tooltip,
  useMapEvents,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

// ── Leaflet Icon Fix for React ──
const defaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});
L.Marker.prototype.options.icon = defaultIcon;

interface LeafletMapProps {
  latitude: number;
  longitude: number;
  onMapClick: (lat: number, lng: number) => void;
  centroids: Array<{ lat: number; lng: number; name: string }>;
}

// Click listener inside Leaflet context
function MapEvents({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

// Controller to fly/pan to selected coordinate programmatically
function MapController({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  return null;
}

export default function LeafletMap({
  latitude,
  longitude,
  onMapClick,
  centroids,
}: LeafletMapProps) {
  const centerPosition: [number, number] = [latitude, longitude];

  return (
    <div className="w-full h-[320px] rounded-lg overflow-hidden border border-border/50 relative bg-background-dark">
      <MapContainer
        center={[12.9716, 77.5946]}
        zoom={11}
        className="w-full h-full z-0"
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions" target="_blank" rel="noopener noreferrer">CARTO</a>'
        />

        {/* Dynamic map events */}
        <MapEvents onMapClick={onMapClick} />
        
        {/* Sync map viewport to outside coordinates changes */}
        <MapController center={centerPosition} />

        {/* Selected Incident Marker */}
        <Marker position={centerPosition}>
          <Tooltip permanent direction="top" offset={[0, -40]}>
            <span className="font-mono text-[10px] font-bold">
              Dispatch Pin ({latitude.toFixed(4)}, {longitude.toFixed(4)})
            </span>
          </Tooltip>
        </Marker>

        {/* Centroids circle markers */}
        {centroids.map((c, index) => (
          <CircleMarker
            key={index}
            center={[c.lat, c.lng]}
            radius={5}
            pathOptions={{
              color: "#06b6d4",
              fillColor: "#06b6d4",
              fillOpacity: 0.6,
              weight: 1,
            }}
            eventHandlers={{
              click: (e) => {
                L.DomEvent.stopPropagation(e);
                onMapClick(c.lat, c.lng);
              },
            }}
          >
            <Tooltip direction="top" offset={[0, -5]}>
              <span className="font-sans text-[11px] font-medium text-foreground">
                Centroid: {c.name}
              </span>
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
