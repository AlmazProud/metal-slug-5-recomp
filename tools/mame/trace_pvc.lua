-- Trace of the NEO-PVC cartridge chip as the 68000 sees it in MAME (adapted from the Metal Slug 3
-- port's trace_sma.lua, MIT, Copyright (c) 2026 AlmazProud).
--
-- Records the writes to the cartridge's P2 space (0x200000-0x2FFFFF: ROM, so any write there is a
-- chip register) and the reads of its top 8 KB (0x2FE000-0x2FFFFF, where the chip's registers are
-- expected), with the frame, the PC and the value.
--
-- Output ($PD_TRACE, trace_pvc.txt by default), written when MAME stops:
--   W <frame> <pc> <address> <data> <mask>      writes, up to $PD_MAX_LINES (4096) per address
--   R <frame> <pc> <address> <data>             reads, up to $PD_MAX_LINES per address
--   S W|R <address> n=<n> distinct=<n> pcs=<pc,...>   per-address summary (all accesses counted)
-- Optional:
--   PD_PLAY=1 inserts a coin and starts a one-player game (then right + fire);
--   PD_SCREENSHOT_FRAMES=a,b,... and PD_PREFIX take screenshots at those frames.

local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local scr = manager.machine.screens[":screen"]
local max_lines = tonumber(os.getenv("PD_MAX_LINES") or "4096")
local lines = {}
local stats = {}

local function record(kind, offset, data, mask)
    local key = kind .. string.format("%06X", offset)
    local s = stats[key]
    if not s then s = { n = 0, values = {}, distinct = 0, pcs = {} }; stats[key] = s end
    s.n = s.n + 1
    if not s.values[data] then s.values[data] = true; s.distinct = s.distinct + 1 end
    local pc = cpu.state["PC"].value
    s.pcs[pc] = true
    if s.n <= max_lines then
        if kind == "W" then
            lines[#lines + 1] = string.format("W %d %06X %06X %04X %04X", scr:frame_number(), pc, offset, data, mask)
        else
            lines[#lines + 1] = string.format("R %d %06X %06X %04X", scr:frame_number(), pc, offset, data)
        end
    end
end

pvc_wtap = mem:install_write_tap(0x200000, 0x2FFFFF, "pd_pvc_w", function(offset, data, mask)
    record("W", offset, data, mask)
end)
pvc_rtap = mem:install_read_tap(0x2FE000, 0x2FFFFF, "pd_pvc_r", function(offset, data, mask)
    record("R", offset, data, mask)
end)

local shots = {}
for n in string.gmatch(os.getenv("PD_SCREENSHOT_FRAMES") or "", "%d+") do shots[tonumber(n)] = true end
local prefix = os.getenv("PD_PREFIX") or "pvc"

local fields = {}
for _, port in pairs(manager.machine.ioport.ports) do
    for name, field in pairs(port.fields) do fields[name] = field end
end
local play = os.getenv("PD_PLAY") == "1"
local script = { [2600] = "Coin 1", [2800] = "1 Player Start", [3100] = "1 Player Start",
                 [3400] = "P1 Button 1", [3700] = "P1 Button 1" }
local release = {}
pvc_frame = emu.add_machine_frame_notifier(function()
    local f = scr:frame_number()
    if shots[f] then scr:snapshot(string.format("%s_%06d.png", prefix, f)) end
    if not play then return end
    local n = script[f]
    if n and fields[n] then fields[n]:set_value(1); release[f + 6] = fields[n] end
    if release[f] then release[f]:set_value(0); release[f] = nil end
    if f > 4000 and fields["P1 Right"] then
        fields["P1 Right"]:set_value(1)
        if fields["P1 Button 1"] then fields["P1 Button 1"]:set_value((f // 8) % 2) end
        if fields["P1 Button 2"] then fields["P1 Button 2"]:set_value((f // 64) % 2) end
    end
end)

pvc_stop = emu.add_machine_stop_notifier(function()
    local f = io.open(os.getenv("PD_TRACE") or "trace_pvc.txt", "w")
    for _, l in ipairs(lines) do f:write(l, "\n") end
    local keys = {}
    for k in pairs(stats) do keys[#keys + 1] = k end
    table.sort(keys)
    for _, k in ipairs(keys) do
        local s = stats[k]
        local pcs = {}
        for pc in pairs(s.pcs) do pcs[#pcs + 1] = string.format("%06X", pc) end
        table.sort(pcs)
        f:write(string.format("S %s %s n=%d distinct=%d pcs=%s\n", k:sub(1, 1), k:sub(2), s.n, s.distinct,
            table.concat(pcs, ",")))
    end
    f:close()
end)
