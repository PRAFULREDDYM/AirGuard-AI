"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Home, Plus, ChevronRight, Wind, Thermometer, Droplets } from "lucide-react";
import { api } from "@/lib/api";

export default function RoomsPage() {
  const [homes, setHomes] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [name, setName] = useState("");
  const [roomType, setRoomType] = useState("living_room");
  const [floor, setFloor] = useState(1);
  const [loading, setLoading] = useState(true);

  const loadRooms = async () => {
    try {
      const h = await api.getHomes();
      setHomes(h);
      if (h.length > 0) {
        const r = await api.getRooms(h[0].id);
        setRooms(r);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRooms();
  }, []);

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || homes.length === 0) return;
    await api.createRoom({
      home_id: homes[0].id,
      name,
      room_type: roomType,
      floor: Number(floor)
    });
    setName("");
    setShowAdd(false);
    loadRooms();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Rooms & Zones</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage multi-room environmental monitoring and targeted room air purification.
          </p>
        </div>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          Add Room
        </button>
      </div>

      {/* Add Room Modal / Collapsible Form */}
      {showAdd && (
        <form onSubmit={handleCreateRoom} className="p-5 rounded-2xl bg-card border border-border shadow-sm space-y-4 max-w-lg">
          <h2 className="text-base font-bold">Add New Room</h2>
          <div>
            <label className="text-xs font-medium block text-muted-foreground mb-1">Room Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Home Office, Nursery, Kitchen"
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium block text-muted-foreground mb-1">Room Type</label>
              <select
                value={roomType}
                onChange={(e) => setRoomType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="living_room">Living Room</option>
                <option value="bedroom">Bedroom</option>
                <option value="kitchen">Kitchen</option>
                <option value="office">Office</option>
                <option value="basement">Basement</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium block text-muted-foreground mb-1">Floor Level</label>
              <input
                type="number"
                value={floor}
                onChange={(e) => setFloor(Number(e.target.value))}
                min={-2}
                max={50}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowAdd(false)}
              className="px-3 py-2 rounded-lg border border-border text-xs font-medium hover:bg-muted"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-3.5 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90"
            >
              Save Room
            </button>
          </div>
        </form>
      )}

      {/* Room Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {rooms.map((room) => (
          <Link
            key={room.id}
            href={`/rooms/${room.id}`}
            className="p-6 rounded-2xl bg-card border border-border hover:border-primary/50 transition-all shadow-sm hover:shadow group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="font-bold text-lg group-hover:text-primary transition-colors">
                  {room.name}
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
                  Floor {room.floor}
                </span>
              </div>
              <span className="text-xs text-muted-foreground block mt-1 capitalize">
                {room.room_type.replace("_", " ")}
              </span>

              <div className="mt-6 grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-muted/40">
                  <span className="text-muted-foreground text-[11px] block">Target PM2.5</span>
                  <span className="text-base font-bold">{room.target_pm25} µg/m³</span>
                </div>
                <div className="p-3 rounded-xl bg-muted/40">
                  <span className="text-muted-foreground text-[11px] block">Air Safety</span>
                  <span className="text-base font-bold text-emerald-500">Normal</span>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-border mt-6 flex items-center justify-between text-xs text-muted-foreground">
              <span>View live room telemetry</span>
              <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

