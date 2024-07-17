import unittest
from business_logic.pdf_operations import calculate_optimal_layout

class TestCalculateOptimalLayout(unittest.TestCase):
    def test_calculate_optimal_layout(self):
        # Test case 1: Standard case - No rotation
        result = calculate_optimal_layout(50, 70, 500, 700, 10)
        self.assertEqual(result['total'], 81)
        self.assertEqual(result['cols'], 9)
        self.assertEqual(result['rows'], 9)
        self.assertEqual(result['card_width'], 50)
        self.assertEqual(result['card_height'], 70)
        self.assertAlmostEqual(result['x_spacing'], 3, places=2)
        self.assertAlmostEqual(result['y_spacing'], 5, places=2)

        # Test case 2: Standard case - With rotation
        result = calculate_optimal_layout(4, 6, 8.5, 11, .25)
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['cols'], 1)
        self.assertEqual(result['rows'], 2)
        self.assertEqual(result['card_width'], 6)
        self.assertEqual(result['card_height'], 4)
        self.assertAlmostEqual(result['x_spacing'], 1, places=2)
        self.assertAlmostEqual(result['y_spacing'], 2.5/3, places=2)

        # Test case 3: Edge case - Square paper and cards
        result = calculate_optimal_layout(100, 100, 1000, 1000, 10)
        self.assertEqual(result['total'], 81)
        self.assertEqual(result['cols'], 9)
        self.assertEqual(result['rows'], 9)
        self.assertEqual(result['card_width'], 100)
        self.assertEqual(result['card_height'], 100)
        self.assertAlmostEqual(result['x_spacing'], 8.89, places=2)
        self.assertAlmostEqual(result['y_spacing'], 8.89, places=2)

        # Test case 4: Edge case - Cards larger than paper
        result = calculate_optimal_layout(600, 800, 500, 700, 10)
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['cols'], 0)
        self.assertEqual(result['rows'], 0)
        self.assertEqual(result['card_width'], 600)
        self.assertEqual(result['card_height'], 800)
        self.assertAlmostEqual(result['x_spacing'], 0.0, places=2)
        self.assertAlmostEqual(result['y_spacing'], 0.0, places=2)

    def test_cards_not_touching(self):
        # Test case 1: Standard case - Cards not touching
        result = calculate_optimal_layout(50, 70, 500, 700, 10)
        self.assertGreater(result['x_spacing'], 0)
        self.assertGreater(result['y_spacing'], 0)

        # Test case 2: Standard case - Cards not touching with rotation
        result = calculate_optimal_layout(80, 120, 800, 1200, 20)
        self.assertGreater(result['x_spacing'], 0)
        self.assertGreater(result['y_spacing'], 0)

        # Test case 3: Edge case - Minimum spacing
        result = calculate_optimal_layout(50, 70, 500, 700, 1)
        self.assertGreater(result['x_spacing'], 0)
        self.assertGreater(result['y_spacing'], 0)

        # Test case 4: Edge case - Cards tightly packed
        result = calculate_optimal_layout(100, 100, 1000, 1000, 0)
        self.assertAlmostEqual(result['x_spacing'], 0, places=2)
        self.assertAlmostEqual(result['y_spacing'], 0, places=2)

    def test_optimal_layout_with_spacing(self):
        # Test case 1: Standard case - Optimal layout with spacing
        result = calculate_optimal_layout(50, 70, 500, 700, 10)
        expected_total = (500 - 2 * 10) // 50 * (700 - 2 * 10) // 70
        self.assertEqual(result['total'], expected_total)

        # Test case 2: Standard case - Optimal layout with spacing and rotation
        result = calculate_optimal_layout(80, 120, 800, 1200, 20)
        expected_total = (800 - 2 * 20) // 80 * (1200 - 2 * 20) // 120
        self.assertEqual(result['total'], expected_total)

        # Test case 3: Edge case - Optimal layout with minimum spacing
        result = calculate_optimal_layout(50, 70, 500, 700, 1)
        expected_total = (500 - 2 * 1) // 50 * (700 - 2 * 1) // 70
        self.assertEqual(result['total'], expected_total)

        # Test case 4: Edge case - Optimal layout with tight packing
        result = calculate_optimal_layout(100, 100, 1000, 1000, 0)
        expected_total = (1000 - 2 * 0) // 100 * (1000 - 2 * 0) // 100
        self.assertEqual(result['total'], expected_total)

if __name__ == '__main__':
    unittest.main()
