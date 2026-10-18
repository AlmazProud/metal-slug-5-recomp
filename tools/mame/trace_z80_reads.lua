-- Every Z80 program-space read (opcode fetches and operands) and every 68000 write to the sound
-- latch (0x320000) in MAME, with the exact time, within PD_FROM_US-PD_TO_US. For instruction-level
-- Z80 timing where the debugger trace gives no cycle counts. Output: PD_TRACE, lines
-- "<us> R <address> <data>" and "<us> CMD68K <value>".
if pd_z80_reads_loaded then return end
pd_z80_reads_loaded = true
local prog = manager.machine.devices[":audiocpu"].spaces["program"]
local m68k = manager.machine.devices[":maincpu"].spaces["program"]
local first = tonumber(os.getenv("PD_FROM_US") or "0")
local last = tonumber(os.getenv("PD_TO_US") or "1e12")
local lines = {}
local function now() return manager.machine.time:as_double() * 1e6 end
z80r_tap = prog:install_read_tap(0x0000, 0xFFFF, "pd_z80r", function(offset, data, mask)
    local t = now()
    if t >= first and t <= last then lines[#lines + 1] = string.format("%.3f R %04X %02X", t, offset, data & 0xFF) end
end)
cmd68_tap = m68k:install_write_tap(0x320000, 0x320001, "pd_cmd68", function(offset, data, mask)
    local t = now()
    if t >= first and t <= last and mask & 0xFF00 ~= 0 then lines[#lines + 1] = string.format("%.3f CMD68K %02X", t, data >> 8) end
end)
z80r_stop = emu.add_machine_stop_notifier(function()
    local f = io.open(os.getenv("PD_TRACE") or "trace_z80_reads.txt", "w")
    for _, s in ipairs(lines) do f:write(s .. "\n") end
    f:close()
end)
