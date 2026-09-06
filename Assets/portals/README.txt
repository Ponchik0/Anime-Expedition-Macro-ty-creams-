Portal mode reference crops

Create one folder per Portal name and place one or more PNG crops of that
Portal's selectable row/card inside it, for example:

  Assets/portals/My Portal/My Portal.png

The folder name appears in Task > Portal > Portal. You can create it from
Settings > General > Image Manager > Portals.

Portal mode also needs two crops in Image Manager > UI Buttons:

  choose_portal  - result-screen button replacing Repeat Stage
  portal_window  - Portal Selection title/anchor proving the picker is open
  portal_confirm - green Select button after highlighting a Portal

The first Portal stage must already be open when the task starts. Each later
repeat is selected automatically through Choose Portal.

Final three-card reward choice

After confirming the inventory Portal, Host mode also expects these UI crops:

  portal_reward_window       - the "Tier 5 Summer Portal" heading above the 3 cards
  portal_modifier_traitless  - "Traitless" in the hovered card's detail sidebar

The macro hovers the three cards from left to right. Task > Portal Blacklist
controls which modifiers are rejected; Traitless is enabled by default.
