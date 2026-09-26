/** «4.83 → 4,8»: одна цифра после запятой, десятичный разделитель — запятая. */
export function formatRating(value: number): string {
  return value.toFixed(1).replace('.', ',')
}

/** «1 → 1-е место». */
export function placeLabel(place: number): string {
  return `${place}-е место`
}
