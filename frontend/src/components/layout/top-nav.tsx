import Link from "next/link"

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/history", label: "History" },
  { href: "/settings", label: "Settings" },
]

export default function TopNav() {
  return (
    <nav className="flex items-center gap-6 text-sm font-semibold text-muted-foreground">
      {navItems.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className="transition-colors hover:text-foreground"
        >
          {item.label}
        </Link>
      ))}
    </nav>
  )
}
