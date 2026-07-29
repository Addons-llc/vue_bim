export const featuredProducts = [
  {
    id: 1,
    name: 'Red Apples',
    category: 'Fruits',
    description: 'Crisp imported apples selected for freshness.',
    price: 12,
    oldPrice: 16,
    rating: 4.8,
    deliveryTime: '12 min',
    image:
      'https://images.unsplash.com/photo-1610832958506-aa56368176cf?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Apples',
  },
  {
    id: 2,
    name: 'Fresh Tomatoes',
    category: 'Vegetables',
    description: 'Firm red tomatoes for salads, curries, and sauces.',
    price: 7,
    oldPrice: 10,
    rating: 4.7,
    deliveryTime: '10 min',
    image:
      'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Tomato',
  },
  {
    id: 3,
    name: 'Chicken Breast',
    category: 'Meat',
    description: 'Cleaned and packed chicken breast from trusted suppliers.',
    price: 26,
    oldPrice: 32,
    rating: 4.7,
    deliveryTime: '18 min',
    image:
      'https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Meat',
  },
  {
    id: 4,
    name: 'King Fish Steak',
    category: 'Fish',
    description: 'Fresh-cut fish steaks cleaned and ready to cook.',
    price: 34,
    oldPrice: 42,
    rating: 4.9,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1534766555764-ce878a5e3a2b?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Fish',
  },
]

export const vegetableProducts = [
  {
    id: 'veg-tomato',
    name: 'Fresh Tomatoes',
    category: 'Vegetables',
    description: '500 g',
    price: 7,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Tomatoes',
  },
  {
    id: 'veg-potato',
    name: 'Potatoes',
    category: 'Vegetables',
    description: '1 kg',
    price: 6,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Potatoes',
  },
  {
    id: 'veg-onion',
    name: 'Red Onions',
    category: 'Vegetables',
    description: '1 kg',
    price: 8,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1580201092675-a0a6a6cafbb1?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Onions',
  },
  {
    id: 'veg-carrot',
    name: 'Carrots',
    category: 'Vegetables',
    description: '500 g',
    price: 5,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1447175008436-054170c2e979?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Carrots',
  },
  {
    id: 'veg-cucumber',
    name: 'Cucumber',
    category: 'Vegetables',
    description: '500 g',
    price: 6,
    oldPrice: null,
    rating: 4.6,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1604977042946-1eecc30f269e?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Cucumber',
  },
  {
    id: 'veg-capsicum',
    name: 'Green Capsicum',
    category: 'Vegetables',
    description: '250 g',
    price: 5,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Capsicum',
  },
  {
    id: 'veg-spinach',
    name: 'Spinach Bunch',
    category: 'Vegetables',
    description: '1 bunch',
    price: 4,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Spinach',
  },
  {
    id: 'veg-broccoli',
    name: 'Broccoli',
    category: 'Vegetables',
    description: '1 pc',
    price: 12,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1459411621453-7b03977f4bfc?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Broccoli',
  },
]

const dairyProductDetailMap = {
  'dairy-milk': {
    images: [
      'https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1528750997573-59b89d56f4f7?auto=format&fit=crop&w=900&q=80',
    ],
    details: [
      { label: 'Pack size', value: '1 ltr' },
      { label: 'Type', value: 'Full cream milk' },
      { label: 'Storage', value: 'Keep refrigerated' },
      { label: 'Best for', value: 'Tea, coffee, cereal, and daily use' },
    ],
  },
  'dairy-curd': {
    images: [
      'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1488477304112-4944851de03d?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1571212515416-fef01fc43637?auto=format&fit=crop&w=900&q=80',
    ],
    details: [
      { label: 'Pack size', value: '200 g' },
      { label: 'Texture', value: 'Fresh, smooth, and creamy' },
      { label: 'Storage', value: 'Keep refrigerated' },
      { label: 'Best for', value: 'Meals, marinades, and dips' },
    ],
  },
  'dairy-butter': {
    images: [
      'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1587132137056-bfbf0166836e?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1603596310923-dbb12732f9c0?auto=format&fit=crop&w=900&q=80',
    ],
    details: [
      { label: 'Pack size', value: '100 g' },
      { label: 'Type', value: 'Salted butter' },
      { label: 'Storage', value: 'Keep chilled after opening' },
      { label: 'Best for', value: 'Toast, baking, and cooking' },
    ],
  },
  'dairy-eggs': {
    images: [
      'https://images.unsplash.com/photo-1506976785307-8732e854ad03?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1598965402089-897ce52e8355?auto=format&fit=crop&w=900&q=80',
    ],
    details: [
      { label: 'Pack size', value: '6 pcs' },
      { label: 'Type', value: 'White eggs' },
      { label: 'Storage', value: 'Keep refrigerated' },
      { label: 'Best for', value: 'Breakfast, baking, and everyday cooking' },
    ],
  },
  'dairy-bread': {
    images: [
      'https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1549931319-a545dcf3bc73?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1533782654613-826a072dd6f3?auto=format&fit=crop&w=900&q=80',
    ],
    details: [
      { label: 'Pack size', value: '300 g' },
      { label: 'Type', value: 'Soft white bread' },
      { label: 'Storage', value: 'Store in a cool, dry place' },
      { label: 'Best for', value: 'Toast, sandwiches, and snacks' },
    ],
  },
  'dairy-cheese': {
    images: [
      'https://images.unsplash.com/photo-1452195100486-9cc805987862?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1552767059-ce182ead6c1b?auto=format&fit=crop&w=900&q=80',
    ],
    details: [
      { label: 'Pack size', value: '200 g' },
      { label: 'Type', value: 'Cheese slices' },
      { label: 'Storage', value: 'Keep refrigerated' },
      { label: 'Best for', value: 'Burgers, sandwiches, and wraps' },
    ],
  },
  'dairy-paneer': {
    images: [
      'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=900&q=80',
    ],
    details: [
      { label: 'Pack size', value: '200 g' },
      { label: 'Type', value: 'Fresh paneer' },
      { label: 'Storage', value: 'Keep refrigerated' },
      { label: 'Best for', value: 'Curries, grills, and snacks' },
    ],
  },
  'dairy-yogurt': {
    images: [
      'https://images.unsplash.com/photo-1488477304112-4944851de03d?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=900&q=80',
    ],
    details: [
      { label: 'Pack size', value: '400 g' },
      { label: 'Type', value: 'Greek yogurt' },
      { label: 'Storage', value: 'Keep refrigerated' },
      { label: 'Best for', value: 'Breakfast bowls, smoothies, and dips' },
    ],
  },
}

export const dairyProducts = [
  {
    id: 'dairy-milk',
    name: 'Fresh Full Cream Milk',
    category: 'Dairy, Bread & Eggs',
    description: '1 ltr',
    price: 7,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Milk',
  },
  {
    id: 'dairy-curd',
    name: 'Fresh Cup Curd',
    category: 'Dairy, Bread & Eggs',
    description: '200 g',
    price: 5,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Curd',
  },
  {
    id: 'dairy-butter',
    name: 'Salted Butter',
    category: 'Dairy, Bread & Eggs',
    description: '100 g',
    price: 9,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Butter',
  },
  {
    id: 'dairy-eggs',
    name: 'White Eggs',
    category: 'Dairy, Bread & Eggs',
    description: '6 pcs',
    price: 10,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1506976785307-8732e854ad03?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Eggs',
  },
  {
    id: 'dairy-bread',
    name: 'White Bread',
    category: 'Dairy, Bread & Eggs',
    description: '300 g',
    price: 6,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Bread',
  },
  {
    id: 'dairy-cheese',
    name: 'Cheese Slices',
    category: 'Dairy, Bread & Eggs',
    description: '200 g',
    price: 14,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1452195100486-9cc805987862?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Cheese',
  },
  {
    id: 'dairy-paneer',
    name: 'Fresh Paneer',
    category: 'Dairy, Bread & Eggs',
    description: '200 g',
    price: 12,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Paneer',
  },
  {
    id: 'dairy-yogurt',
    name: 'Greek Yogurt',
    category: 'Dairy, Bread & Eggs',
    description: '400 g',
    price: 15,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1488477304112-4944851de03d?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Yogurt',
  },
].map((product) => ({
  ...product,
  ...(dairyProductDetailMap[product.id] || {}),
}))

export const fruitProducts = [
  {
    id: 'fruit-apple',
    name: 'Red Apples',
    category: 'Fruits',
    description: '1 kg',
    price: 12,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1567306226416-28f0efdc88ce?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Apples',
  },
  {
    id: 'fruit-banana',
    name: 'Bananas',
    category: 'Fruits',
    description: '1 dozen',
    price: 9,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1603833665858-e61d17a86224?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Bananas',
  },
  {
    id: 'fruit-orange',
    name: 'Oranges',
    category: 'Fruits',
    description: '1 kg',
    price: 11,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1582979512210-99b6a53386f9?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Oranges',
  },
  {
    id: 'fruit-grapes',
    name: 'Green Grapes',
    category: 'Fruits',
    description: '500 g',
    price: 14,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1537640538966-79f369143f8f?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Grapes',
  },
  {
    id: 'fruit-mango',
    name: 'Mangoes',
    category: 'Fruits',
    description: '1 kg',
    price: 18,
    oldPrice: null,
    rating: 4.9,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Mangoes',
  },
  {
    id: 'fruit-strawberry',
    name: 'Strawberries',
    category: 'Fruits',
    description: '250 g',
    price: 16,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1464965911861-746a04b4bca6?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Strawberries',
  },
  {
    id: 'fruit-watermelon',
    name: 'Watermelon',
    category: 'Fruits',
    description: '1 pc',
    price: 22,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Watermelon',
  },
  {
    id: 'fruit-pineapple',
    name: 'Pineapple',
    category: 'Fruits',
    description: '1 pc',
    price: 13,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '8 min',
    image:
      'https://images.unsplash.com/photo-1550258987-190a2d41a8ba?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Pineapple',
  },
]

export const meatProducts = [
  {
    id: 'meat-chicken-breast',
    name: 'Chicken Breast',
    category: 'Meat',
    description: '500 g',
    price: 26,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '18 min',
    image:
      'https://images.unsplash.com/photo-1604503468506-a8da13d82791?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Chicken',
  },
  {
    id: 'meat-chicken-drumstick',
    name: 'Chicken Drumsticks',
    category: 'Meat',
    description: '500 g',
    price: 22,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '18 min',
    image:
      'https://images.unsplash.com/photo-1587593810167-a84920ea0781?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Drumsticks',
  },
  {
    id: 'meat-mutton-cubes',
    name: 'Mutton Cubes',
    category: 'Meat',
    description: '500 g',
    price: 42,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Mutton',
  },
  {
    id: 'meat-mince',
    name: 'Fresh Minced Meat',
    category: 'Meat',
    description: '500 g',
    price: 36,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1603048297172-c92544798d5a?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Mince',
  },
  {
    id: 'meat-lamb-chops',
    name: 'Lamb Chops',
    category: 'Meat',
    description: '500 g',
    price: 48,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1602470520998-f4a52199a3d6?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Lamb',
  },
  {
    id: 'meat-chicken-whole',
    name: 'Whole Chicken',
    category: 'Meat',
    description: '1 kg',
    price: 28,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '18 min',
    image:
      'https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Whole Chicken',
  },
  {
    id: 'meat-beef-steak',
    name: 'Beef Steak',
    category: 'Meat',
    description: '400 g',
    price: 44,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1551028150-64b9f398f678?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Steak',
  },
  {
    id: 'meat-kebab',
    name: 'Ready Kebab Mix',
    category: 'Meat',
    description: '500 g',
    price: 32,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '18 min',
    image:
      'https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Kebab',
  },
]

export const fishProducts = [
  {
    id: 'fish-king-steak',
    name: 'King Fish Steak',
    category: 'Fish',
    description: '500 g',
    price: 34,
    oldPrice: null,
    rating: 4.9,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1534766555764-ce878a5e3a2b?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'King Fish',
  },
  {
    id: 'fish-salmon',
    name: 'Salmon Fillet',
    category: 'Fish',
    description: '300 g',
    price: 46,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1599084993091-1cb5c0721cc6?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Salmon',
  },
  {
    id: 'fish-prawns',
    name: 'Cleaned Prawns',
    category: 'Fish',
    description: '500 g',
    price: 39,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Prawns',
  },
  {
    id: 'fish-sardine',
    name: 'Fresh Sardines',
    category: 'Fish',
    description: '500 g',
    price: 18,
    oldPrice: null,
    rating: 4.6,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1605651377861-348620a3faae?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Sardines',
  },
  {
    id: 'fish-tilapia',
    name: 'Tilapia Whole',
    category: 'Fish',
    description: '1 kg',
    price: 27,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Tilapia',
  },
  {
    id: 'fish-tuna',
    name: 'Tuna Steak',
    category: 'Fish',
    description: '400 g',
    price: 38,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1615141982883-c7ad0e69fd62?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Tuna',
  },
  {
    id: 'fish-squid',
    name: 'Cleaned Squid',
    category: 'Fish',
    description: '500 g',
    price: 31,
    oldPrice: null,
    rating: 4.7,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1559737558-2f5a35f4523b?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Squid',
  },
  {
    id: 'fish-hamour',
    name: 'Hamour Fillet',
    category: 'Fish',
    description: '500 g',
    price: 44,
    oldPrice: null,
    rating: 4.8,
    deliveryTime: '20 min',
    image:
      'https://images.unsplash.com/photo-1524704654690-b56c05c78a00?auto=format&fit=crop&w=400&q=80',
    imageLabel: 'Hamour',
  },
]

export const categories = [
  {
    id: 1,
    name: 'Paan Corner',
    itemGroup: 'Paan Corner',
    image:
      'https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 2,
    name: 'Dairy, Bread & Eggs',
    itemGroup: 'Dairy',
    image:
      'https://images.unsplash.com/photo-1628088062854-d1870b4553da?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 3,
    name: 'Fruits & Vegetables',
    itemGroup: 'Vegetables',
    image:
      'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 4,
    name: 'Cold Drinks & Juices',
    itemGroup: 'Cold Drinks',
    image:
      'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 5,
    name: 'Snacks & Munchies',
    itemGroup: 'Snacks',
    image:
      'https://images.unsplash.com/photo-1621939514649-280e2ee25f60?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 6,
    name: 'Breakfast & Instant Food',
    itemGroup: 'Breakfast',
    image:
      'https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 7,
    name: 'Sweet Tooth',
    itemGroup: 'Sweets',
    image:
      'https://images.unsplash.com/photo-1481391319762-47dff72954d9?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 8,
    name: 'Bakery & Biscuits',
    itemGroup: 'Bakery',
    image:
      'https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 9,
    name: 'Tea, Coffee & Milk Drinks',
    itemGroup: 'Beverages',
    image:
      'https://images.unsplash.com/photo-1447933601403-0c6688de566e?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 10,
    name: 'Atta, Rice & Dal',
    itemGroup: 'Grocery',
    image:
      'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 11,
    name: 'Masala, Oil & More',
    itemGroup: 'Masala',
    image:
      'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 12,
    name: 'Sauces & Spreads',
    itemGroup: 'Sauces',
    image:
      'https://images.unsplash.com/photo-1472476443507-c7a5948772fc?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 13,
    name: 'Chicken, Meat & Fish',
    itemGroup: 'Meat',
    image:
      'https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 14,
    name: 'Organic & Healthy Living',
    itemGroup: 'Organic',
    image:
      'https://images.unsplash.com/photo-1505576399279-565b52d4ac71?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 15,
    name: 'Baby Care',
    itemGroup: 'Baby Care',
    image:
      'https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 16,
    name: 'Pharma & Wellness',
    itemGroup: 'Pharma',
    image:
      'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 17,
    name: 'Cleaning Essentials',
    itemGroup: 'Cleaning',
    image:
      'https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 18,
    name: 'Home & Office',
    itemGroup: 'Home',
    image:
      'https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 19,
    name: 'Personal Care',
    itemGroup: 'Personal Care',
    image:
      'https://images.unsplash.com/photo-1571781926291-c477ebfd024b?auto=format&fit=crop&w=300&q=80',
  },
  {
    id: 20,
    name: 'Pet Care',
    itemGroup: 'Pet Care',
    image:
      'https://images.unsplash.com/photo-1589924691995-400dc9ecc119?auto=format&fit=crop&w=300&q=80',
  },
]
