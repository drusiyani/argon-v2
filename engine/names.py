"""Display names for the four rules (20 Nov 2026). The code, the ledger and every trade id keep the original short ids
(quantlab, noiseband, atrband, expiry), so nothing booked or hashed changes; only what people read does."""
NAMES = {'quantlab': 'Opening Drive', 'noiseband': 'Noise Breakout', 'atrband': 'Range Breakout', 'expiry': 'Expiry Reversal'}
def name(sid): return NAMES.get(sid, sid)
