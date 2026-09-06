Reference images for the Advanced reward-card picker (Cards tab).

One folder per card name, exactly matching the card list on the Cards tab,
e.g.  Assets/cards/EXP Collector/EXP Collector.png

Advanced Card Select checks these images FIRST (template matching), then
falls back to reading each card's name text (OCR) and rarity color. No
images are required -- the OCR pass works on its own -- but a cropped
screenshot of a card makes its detection near-perfect.

Add images from inside the app: Cards tab > a priority card's "+ Image"
button (or Settings > General > Image Manager > Upgrade Cards). Extra
variants of the same card go in the same folder as <name>_alt2.png etc.
