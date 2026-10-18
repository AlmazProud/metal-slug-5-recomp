-- Trace of the NEO-SMA chip as the 68000 sees it in MAME.
--
-- Records every write to the P2 window (0x200000-0x2FFFFF: the cartridge ROM space, so any write
-- there is a chip register) and every read of its top 8 KB (0x2FE000-0x2FFFFF, where the chip's
-- registers are expected), with the PC and the value.
--
-- Output ($PD_TRACE, trace_sma.txt by default), written when MAME stops:
--   W <frame> <pc> <address> <data> <mask>      every write (all of them)
--   R <frame> <pc> <address> <data>             reads of an address, up to $PD_MAX_READS (4096)
--                                               per address; the rest are only counted
--   S <address> reads=<n> distinct=<n> pcs=<pc,...>   per-address summary
-- Optional: PD_PLAY=1 inserts a coin and starts a one-player game.

local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local scr = manager.machine.screens[":screen"]
local max_reads = tonumber(os.getenv("PD_MAX_READS") or "4096")
local lines = {}
local reads = {}

sma_wtap = mem:install_write_tap(0x200000, 0x2FFFFF, "pd_sma_w", function(offset, data, mask)
    lines[#lines + 1] = string.format("W %d %06X %06X %04X %04X", scr:frame_number(),
        cpu.state["PC"].value, offset, data, mask)
end)

sma_rtap = mem:install_read_tap(0x2FE000, 0x2FFFFF, "pd_sma_r", function(offset, data, mask)
    local r = reads[offset]
    if not r then r = { n = 0, values = {}, distinct = 0, pcs = {} }; reads[offset] = r end
    r.n = r.n + 1
    if not r.values[data] then r.values[data] = true; r.distinct = r.distinct + 1 end
    local pc = cpu.state["PC"].value
    r.pcs[pc] = true
    if r.n <= max_reads then
        lines[#lines + 1] = string.format("R %d %06X %06X %04X", scr:frame_number(), pc, offset, data)
    end
end)

if os.getenv("PD_PLAY") == "1" then
    local fields = {}
    for _, port in pairs(manager.machine.ioport.ports) do
        for name, field in pairs(port.fields) do fields[name] = field end
    end
    -- Coin, start, then hold right and fire now and then.
    local script = { [2600] = "Coin 1", [2800] = "1 Player Start", [3100] = "1 Player Start",
                     [3400] = "P1 Button 1", [3700] = "P1 Button 1" }
    local release = {}
    sma_play = emu.add_machine_frame_notifier(function()
        local f = scr:frame_number()
        local n = script[f]
        if n and fields[n] then fields[n]:set_value(1); release[f + 6] = fields[n] end
        if release[f] then release[f]:set_value(0); release[f] = nil end
        if f > 4000 and fields["P1 Right"] then
            fields["P1 Right"]:set_value(1)
            if fields["P1 Button 1"] then fields["P1 Button 1"]:set_value((f // 8) % 2) end
        end
    end)
end

sma_stop = emu.add_machine_stop_notifier(function()
    local f = io.open(os.getenv("PD_TRACE") or "trace_sma.txt", "w")
    for _, l in ipairs(lines) do f:write(l, "\n") end
    for addr, r in pairs(reads) do
        local pcs = {}
        for pc in pairs(r.pcs) do pcs[#pcs + 1] = string.format("%06X", pc) end
        table.sort(pcs)
        f:write(string.format("S %06X reads=%d distinct=%d pcs=%s\n", addr, r.n, r.distinct,
            table.concat(pcs, ",")))
    end
    f:close()
end)
