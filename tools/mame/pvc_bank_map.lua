-- Black-box map of the NEO-PVC bank registers (adapted from the Metal Slug 3 port's
-- sma_bank_map.lua, MIT, Copyright (c) 2026 AlmazProud): for each register in $PD_BANK_REGS
-- (default "2FFFF0,2FFFF2"), writes every 16-bit value to it while the other registers hold the
-- values in $PD_BANK_HOLD (default "2FFFF0=0000,2FFFF2=1000"), and samples what the 68000 then
-- sees in the P2 window (0x200000-0x2FFFFF).
--
-- Output ($PD_TRACE, pvc_bank_map.txt by default), one line per register and value:
--   <register> <value> <hex of 8 bytes at 0x200000 + k * 0x10000, k = 0..15>
-- (bytes in 68000 order). tools/pvc_banks.py locates every sample in the program region.

local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]

local regs, hold = {}, {}
for r in string.gmatch(os.getenv("PD_BANK_REGS") or "2FFFF0,2FFFF2", "%x+") do regs[#regs + 1] = tonumber(r, 16) end
for r, v in string.gmatch(os.getenv("PD_BANK_HOLD") or "2FFFF0=0000,2FFFF2=1000", "(%x+)=(%x+)") do
    hold[#hold + 1] = { tonumber(r, 16), tonumber(v, 16) }
end

bank_frame = emu.add_machine_frame_notifier(function()
    if manager.machine.screens[":screen"]:frame_number() ~= 2 then return end
    local f = io.open(os.getenv("PD_TRACE") or "pvc_bank_map.txt", "w")
    for _, reg in ipairs(regs) do
        for v = 0, 0xFFFF do
            for _, h in ipairs(hold) do
                if h[1] ~= reg then mem:write_u16(h[1], h[2]) end
            end
            mem:write_u16(reg, v)
            local parts = { string.format("%06X %04X ", reg, v) }
            for k = 0, 15 do
                local base = 0x200000 + k * 0x10000
                for i = 0, 7, 2 do parts[#parts + 1] = string.format("%04X", mem:read_u16(base + i)) end
            end
            f:write(table.concat(parts), "\n")
        end
    end
    f:close()
    manager.machine:exit()
end)
