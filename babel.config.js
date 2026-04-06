module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      [
        'module-resolver',
        {
          root: ['./'],
          alias: {
            '@': './src',
            '@components': './src/components',
            '@screens': './src/screens',
            '@services': './src/services',
            '@types': './src/types',
            '@store': './src/store',
            '@utils': './src/utils',
            '@constants': './src/constants',
            '@hooks': './src/hooks',
            '@assets': './assets',
          },
        },
      ],
    ],
  };
};
