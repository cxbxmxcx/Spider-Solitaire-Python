import pygame
import sys
import random
import os

pygame.init()

infoObject = pygame.display.Info()
WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Spider Solitaire with Images")

# # --- Window and Layout Setup ---
# WIDTH, HEIGHT = 2200, 1200
# screen = pygame.display.set_mode((WIDTH, HEIGHT))
# pygame.display.set_caption("Spider Solitaire with Images")

font = pygame.font.SysFont("Arial", 20)
clock = pygame.time.Clock()

# Set card dimensions.
# (Adjust these as needed for your image set.)
CARD_WIDTH = 160
CARD_HEIGHT = 240
CARD_MARGIN = 5
CARD_SPACING = 60  # vertical spacing between cards in tableau
X_OFFSET = 20      # left margin for each tableau column

# Top area reserved for draw pile and completed sets.
TOP_AREA_HEIGHT = 250
TABLEAU_Y_OFFSET = TOP_AREA_HEIGHT + 20

# Draw pile area (top left)
DRAW_PILE_RECT = pygame.Rect(10, 10, CARD_WIDTH, CARD_HEIGHT)
# Reset button (bottom center)
RESET_BUTTON_RECT = pygame.Rect(WIDTH // 2 - 50, HEIGHT - 50, 100, 40)

# --- Image Loading Functions ---
# Caches for images.
card_images = {}
card_back_image = None

def convert_card_value(card_value):
    """
    Converts a card code (e.g., "KH", "AS", "10D") to a full name.
    Example:
      "KH" -> "king_of_hearts"
      "AS" -> "ace_of_spades"
      "10D" -> "10_of_diamonds"
    """
    # Extract the rank and suit parts.
    rank = card_value[:-1]
    suit = card_value[-1]

    # Mapping of card ranks to full names.
    rank_map = {
        "A": "ace",
        "2": "2",
        "3": "3",
        "4": "4",
        "5": "5",
        "6": "6",
        "7": "7",
        "8": "8",
        "9": "9",
        "10": "10",
        "J": "jack",
        "Q": "queen",
        "K": "king"
    }

    # Mapping of suit letters to full names.
    suit_map = {
        "H": "hearts",
        "D": "diamonds",
        "C": "clubs",
        "S": "spades"
    }

    rank_name = rank_map.get(rank, rank)
    suit_name = suit_map.get(suit, suit)

    return f"{rank_name}_of_{suit_name}"


def load_card_image(card_value):
    """
    Loads the card image corresponding to card_value (e.g., "KH"),
    draws it on a white background, and adds a border.
    """
    if card_value in card_images:
        return card_images[card_value]
    else:
        # Use convert_card_value to get the proper filename.
        filename = f"{convert_card_value(card_value)}.png"
        path = os.path.join("cards", filename)
        try:
            # Load the card image (with alpha transparency).
            image = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"Error loading image: {path}", e)
            # Create a placeholder surface if image not found.
            image = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
            image.fill((255, 0, 255))  # Magenta signals error.
        
        # Scale the card image.
        image = pygame.transform.scale(image, (CARD_WIDTH-CARD_MARGIN*2, CARD_HEIGHT-CARD_MARGIN*2))
        
        # Create a new surface with a white background.
        white_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        white_back.fill((255, 255, 255))
        
        # Blit the loaded card image onto the white background.
        white_back.blit(image, (CARD_MARGIN, CARD_MARGIN))
        
        # Draw a border on the card.
        border_color = (0, 0, 0)      # Black border.
        border_thickness = 2          # Thickness in pixels.
        pygame.draw.rect(white_back, border_color, white_back.get_rect(), border_thickness)
        
        # Cache and return the final image.
        card_images[card_value] = white_back
        return white_back

def load_card_back():
    global card_back_image
    if card_back_image is not None:
        return card_back_image
    else:
        path = os.path.join("cards", "back.png")
        try:
            # Load the card back image (with alpha transparency).
            image = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"Error loading card back image: {path}", e)
            # Create a placeholder surface if the image is not found.
            image = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
            image.fill((50, 50, 50))
        
        # Scale the card back image.
        image = pygame.transform.scale(image, (CARD_WIDTH, CARD_HEIGHT))
        
        # Create a new surface with a white background.
        white_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        white_back.fill((255, 255, 255))
        
        # Blit the card back image onto the white background.
        white_back.blit(image, (0, 0))
        
        # Draw a border around the card.
        border_color = (0, 0, 0)      # Black border.
        border_thickness = 2          # Thickness in pixels.
        pygame.draw.rect(white_back, border_color, white_back.get_rect(), border_thickness)
        
        # Cache and return the final card back image.
        card_back_image = white_back
        return card_back_image

# --- Card Class and Helper Functions ---
class Card:
    def __init__(self, value, face_up=False):
        self.value = value      # e.g., "KC" for King of Clubs
        self.face_up = face_up  # Whether the card is turned over

    def __repr__(self):
        return f"{self.value}{' (up)' if self.face_up else ' (down)'}"

ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
suits = ['C', 'D', 'H', 'S']
rank_map = {
    'A': 1, '2': 2, '3': 3, '4': 4, '5': 5,
    '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 11, 'Q': 12, 'K': 13
}

def get_rank_suit(card):
    """Return a tuple (numeric rank, suit) for the given card."""
    rank_str = card.value[:-1]
    suit = card.value[-1]
    return rank_map[rank_str], suit

def is_valid_sequence(cards, start_index):
    """
    Returns True if the cards from start_index to the end form
    a valid descending sequence in the same suit (and are face up).
    """
    if not cards[start_index].face_up:
        return False
    if start_index >= len(cards) - 1:
        return True
    for i in range(start_index, len(cards) - 1):
        if not (cards[i].face_up and cards[i+1].face_up):
            return False
        rank1, suit1 = get_rank_suit(cards[i])
        rank2, suit2 = get_rank_suit(cards[i+1])
        if rank1 != rank2 + 1 or suit1 != suit2:
            return False
    return True

def check_complete_sequence(col):
    """
    Checks if the last 13 cards in a column form a complete sequence
    from King down to Ace (all face up and same suit). If found,
    removes and returns that sequence; otherwise, returns None.
    """
    if len(col) < 13:
        return None
    seq = col[-13:]
    if not all(card.face_up for card in seq):
        return None
    first_rank, first_suit = get_rank_suit(seq[0])
    if first_rank != 13:  # Must start with a King.
        return None
    for i in range(13):
        rank_val, suit = get_rank_suit(seq[i])
        if suit != first_suit or rank_val != 13 - i:
            return None
    del col[-13:]
    print("Complete sequence removed!")
    return seq

# --- Global Game State Variables ---
columns = []         # 10 tableau columns (each is a list of Card objects)
stock = []           # Draw pile (remaining cards to be dealt)
completed_sets = []  # List of completed sequences (each is a list of 13 Card objects)

dragging = False
dragged_cards = []   # Cards being dragged
dragged_from = None  # (tableau column index, starting card index) for dragged cards
drag_offset = (0, 0) # Offset between mouse click and card's top-left
drag_pos = (0, 0)    # Current position to draw dragged cards

def reset_game():
    """Resets the game: shuffles the deck, deals the tableau, and resets state.
       Only the top card of each tableau column is face up."""
    global columns, stock, completed_sets, dragging, dragged_cards, dragged_from
    deck = [Card(rank + suit, face_up=False) for _ in range(2) for rank in ranks for suit in suits]
    random.shuffle(deck)
    columns = []
    # Deal 10 columns: first 4 get 6 cards, remaining 6 get 5 cards.
    for i in range(10):
        n_cards = 6 if i < 4 else 5
        col = [deck.pop() for _ in range(n_cards)]
        for card in col[:-1]:
            card.face_up = False
        if col:
            col[-1].face_up = True
        columns.append(col)
    stock = deck  # Remaining cards become the draw pile.
    completed_sets.clear()
    dragging = False
    dragged_cards.clear()
    dragged_from = None

# Initialize game.
reset_game()

# --- Main Game Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left-click
                mouse_x, mouse_y = event.pos

                # Check for Reset button click.
                if RESET_BUTTON_RECT.collidepoint(mouse_x, mouse_y):
                    reset_game()
                    continue

                # Check for Draw Pile click.
                if DRAW_PILE_RECT.collidepoint(mouse_x, mouse_y):
                    # A new deal is allowed only if every tableau column is non-empty.
                    if stock and all(len(col) > 0 for col in columns):
                        for col in columns:
                            if stock:
                                card = stock.pop()
                                card.face_up = True
                                col.append(card)
                    continue

                col_width = WIDTH // 10
                # Check for clicks in the tableau.
                for i, col in enumerate(columns):
                    col_x = i * col_width + X_OFFSET
                    # Cards are drawn starting at TABLEAU_Y_OFFSET.
                    for j in range(len(col) - 1, -1, -1):
                        card_x = col_x
                        card_y = TABLEAU_Y_OFFSET + j * CARD_SPACING
                        card_rect = pygame.Rect(card_x, card_y, CARD_WIDTH, CARD_HEIGHT)
                        if card_rect.collidepoint(mouse_x, mouse_y):
                            # Only allow dragging if the card is face up and
                            # the sequence from here is valid.
                            if col[j].face_up and is_valid_sequence(col, j):
                                dragging = True
                                dragged_cards = col[j:]
                                dragged_from = (i, j)
                                del col[j:]
                                drag_offset = (mouse_x - card_x, mouse_y - card_y)
                                drag_pos = (mouse_x - drag_offset[0], mouse_y - drag_offset[1])
                            break
                    if dragging:
                        break

        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                mouse_x, mouse_y = event.pos
                drag_pos = (mouse_x - drag_offset[0], mouse_y - drag_offset[1])

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and dragging:
                mouse_x, mouse_y = event.pos
                col_width = WIDTH // 10
                drop_col_index = mouse_x // col_width
                drop_col_index = max(0, min(9, drop_col_index))
                valid_move = False
                dest_col = columns[drop_col_index]
                if len(dest_col) == 0:
                    valid_move = True
                else:
                    dest_card = dest_col[-1]
                    if dest_card.face_up:
                        dest_rank, _ = get_rank_suit(dest_card)
                        moving_rank, _ = get_rank_suit(dragged_cards[0])
                        if dest_rank == moving_rank + 1:
                            valid_move = True

                if valid_move:
                    columns[drop_col_index].extend(dragged_cards)
                    # If the source column still has cards, flip its new top card face up.
                    orig_col_index, _ = dragged_from
                    if columns[orig_col_index] and not columns[orig_col_index][-1].face_up:
                        columns[orig_col_index][-1].face_up = True
                    # Check for complete sequences.
                    while True:
                        seq = check_complete_sequence(columns[drop_col_index])
                        if seq is None:
                            break
                        completed_sets.append(seq)
                        if columns[drop_col_index] and not columns[drop_col_index][-1].face_up:
                            columns[drop_col_index][-1].face_up = True
                else:
                    # Return dragged cards to the original column.
                    orig_col_index, _ = dragged_from
                    columns[orig_col_index].extend(dragged_cards)
                dragging = False
                dragged_cards = []
                dragged_from = None

    # --- Drawing ---
    screen.fill((0, 128, 0))  # Table felt background

    # Draw the top area.
    pygame.draw.rect(screen, (0, 100, 0), (0, 0, WIDTH, TOP_AREA_HEIGHT))

    # Draw the Draw Pile.
    if stock:
        card_back = load_card_back()
        screen.blit(card_back, (DRAW_PILE_RECT.x, DRAW_PILE_RECT.y))
        count_surface = font.render(str(len(stock)), True, (255, 255, 255))
        screen.blit(count_surface, (DRAW_PILE_RECT.right + 5, DRAW_PILE_RECT.y + 5))
    else:
        pygame.draw.rect(screen, (100, 100, 100), DRAW_PILE_RECT)
        pygame.draw.rect(screen, (0, 0, 0), DRAW_PILE_RECT, 2)
        empty_surface = font.render("Empty", True, (255, 255, 255))
        screen.blit(empty_surface, (DRAW_PILE_RECT.x + 5, DRAW_PILE_RECT.y + 5))

    # Draw Completed Sets in the top area (to the right of the draw pile).
    comp_x = DRAW_PILE_RECT.right + 50
    comp_y = 10
    for seq in completed_sets:
        seq_x = comp_x
        for card in seq:
            face_img = load_card_image(card.value)
            screen.blit(face_img, (seq_x, comp_y))
            seq_x += CARD_WIDTH // 4  # Slight overlap for display.
        comp_x += seq_x + 20

    # Draw tableau columns.
    col_width = WIDTH // 10
    max_visible = 5
    for i, col in enumerate(columns):
        col_x = i * col_width + X_OFFSET
        max_visible = max(max_visible, len(col))
        for j, card in enumerate(col):            
            card_x = col_x
            card_y = TABLEAU_Y_OFFSET + j * CARD_SPACING
            if card.face_up:
                img = load_card_image(card.value)
            else:
                img = load_card_back()
            screen.blit(img, (card_x, card_y))
    CARD_SPACING = min((HEIGHT - TABLEAU_Y_OFFSET) // max_visible, 40)
    # Draw dragged cards.
    if dragging:
        for idx, card in enumerate(dragged_cards):
            card_x = drag_pos[0]
            card_y = drag_pos[1] + idx * CARD_SPACING
            if card.face_up:
                img = load_card_image(card.value)
            else:
                img = load_card_back()
            screen.blit(img, (card_x, card_y))

    # Draw the Reset button.
    pygame.draw.rect(screen, (200, 200, 200), RESET_BUTTON_RECT)
    reset_text = font.render("Reset", True, (0, 0, 0))
    text_rect = reset_text.get_rect(center=RESET_BUTTON_RECT.center)
    screen.blit(reset_text, text_rect)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
