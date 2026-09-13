"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import {
  CalendarDays,
  FileText,
  HeartPulse,
  MessageCircle,
  Plus,
} from "lucide-react"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"

const pages = [
  { href: "/", label: "AI assistant", icon: MessageCircle },
  { href: "/documents", label: "My documents", icon: FileText },
  { href: "/appointments", label: "Appointments", icon: CalendarDays },
]

export default function WorkspaceLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname()
  const router = useRouter()
  const activePage = pages.find((page) => page.href === pathname) ?? pages[0]

  return (
    <SidebarProvider className="min-h-svh">
      <Sidebar collapsible="offcanvas">
        <SidebarHeader className="p-3">
          <SidebarMenu className="gap-2">
            <SidebarMenuItem>
              <SidebarMenuButton size="lg" asChild>
                <Link href="/">
                  <span className="grid size-9 place-items-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                    <HeartPulse />
                  </span>
                  <span className="text-lg font-semibold tracking-tight">
                    mediqare<span className="text-primary">.</span>
                  </span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                onClick={() => router.push(`/?new=${Date.now()}`)}
              >
                <Plus />
                New conversation
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Your space</SidebarGroupLabel>
            <SidebarMenu>
              {pages.map(({ href, label, icon: Icon }) => (
                <SidebarMenuItem key={href}>
                  <SidebarMenuButton asChild isActive={pathname === href}>
                    <Link href={href}>
                      <Icon />
                      {label}
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
        
        </SidebarContent>
      </Sidebar>
      <SidebarInset className="min-h-svh min-w-0">
        <header className="flex h-16 shrink-0 items-center gap-3 border-b px-4 md:px-8">
          <SidebarTrigger />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage>Your space</BreadcrumbPage>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>{activePage.label}</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </header>
        <main className="flex min-h-0 flex-1 flex-col">{children}</main>
      </SidebarInset>
    </SidebarProvider>
  )
}
